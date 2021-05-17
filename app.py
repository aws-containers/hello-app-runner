import py_avataaars
import random, logging, sys
import uvicorn

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
from starlette.config import Config
from starlette.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse, JSONResponse
from starlette_exporter import PrometheusMiddleware, handle_metrics

from json import loads, dumps
from requests import get
from os import getenv, urandom, path, environ
from PIL import Image

templates = Jinja2Templates(directory='templates')

global_state = {
    "INITIALIZED": False
}

logging.basicConfig(stream=sys.stdout, level=eval('logging.' + getenv('LOG_LEVEL', 'INFO')))
logging.debug('Log level is set to DEBUG.')

# Generate and save a local avatar image
def generate_avatar_image():
    logging.info('Generating avatar image')
    custom_circle_colors = [
        'BLUE_01',
        'BLUE_02',
        'PASTEL_BLUE',
        'PASTEL_GREEN',
        'PASTEL_ORANGE',
        'PASTEL_RED',
        'PASTEL_YELLOW',
    ]
    custom_mouth_types = [
        'DEFAULT',
        'EATING',
        'GRIMACE',
        'SMILE',
        'TONGUE',
        'TWINKLE',
    ]
    custom_eyebrow_types = [
        'DEFAULT',
        'DEFAULT_NATURAL',
        'FLAT_NATURAL',
        'RAISED_EXCITED',
        'RAISED_EXCITED_NATURAL',
        'SAD_CONCERNED',
        'SAD_CONCERNED_NATURAL',
        'UNI_BROW_NATURAL',
        'UP_DOWN',
        'UP_DOWN_NATURAL',
        'FROWN_NATURAL',
    ]
    custom_eye_types = [
        'DEFAULT',
        'CLOSE',
        'EYE_ROLL',
        'HAPPY',
        'HEARTS',
        'SIDE',
        'SQUINT',
        'SURPRISED',
        'WINK',
        'WINK_WACKY',
    ]

    # pick a random value from default types
    def r(enum_):
        return random.choice(list(enum_))

    # Make a random customization selection from custom arrays
    def rc(customization, array):
        return eval("py_avataaars." + customization + "." +  random.choice(array))

    avatar = py_avataaars.PyAvataaar(
        style=py_avataaars.AvatarStyle.CIRCLE,
        background_color=rc("Color", custom_circle_colors),
        skin_color=r(py_avataaars.SkinColor),
        hair_color=r(py_avataaars.HairColor),
        facial_hair_type=r(py_avataaars.FacialHairType),
        facial_hair_color=r(py_avataaars.HairColor),
        top_type=r(py_avataaars.TopType),
        hat_color=r(py_avataaars.Color),
        mouth_type=rc("MouthType", custom_mouth_types),
        eye_type=rc("EyesType", custom_eye_types),
        eyebrow_type=rc("EyebrowType", custom_eyebrow_types),
        nose_type=r(py_avataaars.NoseType),
        accessories_type=r(py_avataaars.AccessoriesType),
        clothe_type=r(py_avataaars.ClotheType),
        clothe_color=r(py_avataaars.Color),
        clothe_graphic_type=r(py_avataaars.ClotheGraphicType),
    )

    try:
        avatar.render_png_file('avatar.png')
    except Exception as e:
        logging.ERROR('Could not write avatar file with error: %s', e)

# Generate and save a social media banner image
def generate_social_card(avatar_file):
    logging.info('Generating social card image.')
    # We have two backgrounds to choose from
    base_image_options = ['banner_base_light.png', 'banner_base_dark.png']
    base_image = random.choice(base_image_options)

    # open our images to use them
    background = Image.open(base_image)
    foreground = Image.open(avatar_file)

    # resize the image to 439x439 (default image size is 280x280)
    resized_foreground = foreground.resize((439, 439))

    # placement values for avatar on top of background
    background_width_center = int(background.width * .0258 )
    background_height_center = int(background.height * .145)
    # paste the avatar on top of the background in the right location
    background.paste(resized_foreground, (background_width_center,background_height_center), resized_foreground)
    # save the new image
    try:
        background.save('./static/social.png')
    except Exception as e:
        logging.ERROR('Could not save twitter banner with error: %s', e)

def homepage(request):
    return PlainTextResponse('Hello, world!')

def _setup(request):
    random.seed(str(request.url))
    if not path.isfile('avatar.png'):
        generate_avatar_image()
    if not path.isfile('./static/social.png'):
        generate_social_card('avatar.png')
    global_state["INITIALIZED"] = True

def index(request):
    if "Go-http-client" in request.headers['user-agent']:
        # Filter out health checks from the load balancer
        return PlainTextResponse("healthy")
    if "curl" in request.headers['user-agent']:
        return templates.TemplateResponse('index.txt', {'request': request})
    else:
        if not global_state["INITIALIZED"]:
            _setup(request)
        return templates.TemplateResponse('index.html', {'request': request})

def headers(request):
    return JSONResponse(dumps({k:v for k, v in request.headers.items()}))

routes = [
    Route('/', endpoint=index),
    Route('/headers', endpoint=headers),
    Mount('/static', app=StaticFiles(directory='static'), name='static'),
]

app = Starlette(debug=True, routes=routes)
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

config = Config()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0",
                port=int(getenv('PORT', 8000)),
                log_level=getenv('LOG_LEVEL', "info"),
                debug=getenv('DEBUG', False),
                proxy_headers=True)
