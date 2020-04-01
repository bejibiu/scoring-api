import json
import datetime
import functools
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from scoring import get_score, get_interests
from store import StorageRedis

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"

REDIS_HOST = ''
REDIS_PORT = None
RETRY_CONNECTION = None
TIMEOUT_CONNECTION = None

OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field():
    def __init__(self,  required, nullable=False):
        self.data = None
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, owner):
        return self.data


class CharField(Field):
    def __set__(self, instance, value):
        if value or not self.nullable:
            if not isinstance(value, str):
                raise ValueError(f"{instance.__class__.__name__} must be string!")
        self.data = value


class ArgumentsField(Field):
    def __set__(self, instance, value):
        if value or not self.nullable:
            if not isinstance(value, dict):
                raise ValueError("Argument must be dict!")
        self.data = value


class EmailField(CharField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value and "@" not in value:
            raise ValueError("Email must be contain '@' ")


class PhoneField(Field):
    def __set__(self, instance, value):
        if value or not self.nullable:
            if not (isinstance(value, str) or isinstance(value, int)):
                raise ValueError("Number phone must be str or int")
            if len(str(value)) != 11:
                raise ValueError("Phone numbers must be contain 11 numbers")
            if not self.check_start_with_7(value):
                raise ValueError("Phone must be start with 7")
            value = str(value)
        self.data = value

    def check_start_with_7(self, phone):
        if isinstance(phone, str):
            return phone.startswith('7')
        return (phone // 1_000_000_00_00) == 7


class DateField(CharField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value or not self.nullable:
            try:
                if not datetime.datetime.strptime(value, "%d.%m.%Y"):
                    raise ValueError("Date must be date format DD.MM.YYYY !")
            except ValueError:
                raise ValueError("Date must be date format DD.MM.YYYY !")
            self.data = datetime.datetime.strptime(value, "%d.%m.%Y")


class BirthDayField(DateField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value:
            #  70 year in days = 70 * 365days + 17 days in high-altitude year
            if (datetime.datetime.now() - datetime.datetime.strptime(value, "%d.%m.%Y")).days > 70 * 365 + 17:
                raise ValueError("Age must be less than 70 years old")


class GenderField(Field):
    def __set__(self, instance, value):
        if value or not self.nullable:
            if not isinstance(value, int) or value not in GENDERS.keys():
                raise ValueError("Gender must be 0,1 or 2")
        self.data = value


class ClientIDsField(Field):
    def __set__(self, instance, value):
        if not value or not isinstance(value, list) or not all([isinstance(x, int) for x in value]):
            raise ValueError("Client ids must be list<int>!")
        self.data = value


class Method:
    def __init__(self):
        self.method_fields = [k for k, v in self.__class__.__dict__.items()
                              if isinstance(v, Field)]

    def load_validate_field(self, **kwargs):
        for filed_ in self.method_fields:
            attr = None if filed_ not in kwargs else kwargs[filed_]
            setattr(self, filed_, attr)


class ClientsInterestsRequest(Method):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Method):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def valid_pair(self):
        return any((
            all((self.first_name is not None, self.last_name is not None)),
            all((self.phone is not None, self.email is not None)),
            all((self.birthday is not None, self.gender is not None))
        ))

    def get_list_no_empty_field(self):
        return [key for key in self.method_fields if getattr(self, key) is not None]


class MethodRequest(Method):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode()).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode()).hexdigest()
    if digest == request.token:
        return True
    return False


def auth_req(func):
    @functools.wraps(func)
    def decorator(request, *arg, **kwargs):
        if check_auth(request):
            return func(request, *arg, **kwargs)
        logging.info('Bad auth')
        return ERRORS[FORBIDDEN], FORBIDDEN
    return decorator


@auth_req
def handler_online_score(request, ctx, store):
    onlineScoreRequest = OnlineScoreRequest()
    onlineScoreRequest.load_validate_field(**request.arguments)
    if onlineScoreRequest.valid_pair():
        ctx['has'] = onlineScoreRequest.get_list_no_empty_field()
        if request.is_admin:
            return {"score": 42}, OK
        return {"score": get_score(
            store=store,
            first_name=onlineScoreRequest.first_name,
            last_name=onlineScoreRequest.last_name,
            email=onlineScoreRequest.email,
            phone=onlineScoreRequest.phone,
            birthday=onlineScoreRequest.birthday,
            gender=onlineScoreRequest.gender,
        )}, OK
    raise ValueError("Not one paird is valid")


@auth_req
def handler_client_interests(request, ctx, store):
    clientsInterestsRequest = ClientsInterestsRequest()
    clientsInterestsRequest.load_validate_field(**request.arguments)
    ctx['nclients'] = len(clientsInterestsRequest.client_ids)
    return {client_id: get_interests(store, client_id) for client_id in clientsInterestsRequest.client_ids}, OK


def method_handler(request, ctx, store):
    method_handlers = {
        "online_score": handler_online_score,
        "clients_interests": handler_client_interests
    }
    try:
        method_request = MethodRequest()
        method_request.load_validate_field(**request.get('body'))
    except ValueError as e:
        logging.exception(e)
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    logging.info(f"Method {method_request.method}")
    try:
        response, code = method_handlers[method_request.method](method_request, ctx, store)
    except (ValueError, AttributeError, TypeError) as e:
        logging.exception(e)
        return {"error": e}, INVALID_REQUEST
    else:
        return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = StorageRedis(host=REDIS_HOST, port=REDIS_PORT, timeout_connection=TIMEOUT_CONNECTION, retry_connection=RETRY_CONNECTION)

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except Exception:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-r", "--redis-host", action="store", default='127.0.0.1')
    op.add_option("--redis-port", action="store", type=int, default=6379)
    op.add_option("--retry-connection", action="store", type=int, default=3)
    op.add_option("--timeout-connection", action="store", type=int, default=20)
    (opts, args) = op.parse_args()

    REDIS_HOST = opts.redis_host
    REDIS_PORT = opts.redis_port
    RETRY_CONNECTION = opts.retry_connection
    TIMEOUT_CONNECTION = opts.timeout_connection

    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
