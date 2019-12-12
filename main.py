import threading
import sched
import logging
import time
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.picture_message import PictureMessage
from viberbot.api.bot_configuration import BotConfiguration
from viberbot import Api
from flask import Flask, request, Response
import urllib.request
import os
import face_recognition

auth_token = '4abd2e18a1e7d470-bf895d5fea2629c7-b296bff270dd40bf'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='PythonSampleBot',
    avatar='http://viber.com/avatar.jpg',
    auth_token=auth_token
))

image_dir = '.\\images'
test_image_dir = '.\\images'


@app.route('/', methods=['POST'])
def incoming():
    logger.debug("\n\nreceived request. post data: {0}".format(
        request.get_data()))

    viber_request = viber.parse_request(request.get_data().decode('utf8'))

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message
        if isinstance(message, PictureMessage):
            print('\n\n\n', message.text, message.media)
            image_ext = message.media.split('?')[0].split('.')[-1]
            image_name = message.text if message.text else False
            if bool(image_name):
                urllib.request.urlretrieve(
                    message.media, os.path.join(image_dir, image_name + '.' + image_ext))
            else:
                image_name = 'test' + '.' + image_ext
                urllib.request.urlretrieve(
                    message.media, os.path.join(image_dir, image_name))
                unknown_image = face_recognition.load_image_file(os.path.join(image_dir, image_name))
                face_enc = face_recognition.face_encodings(unknown_image)
                if len(face_enc) == 0:
                    viber.send_messages(viber_request.sender.id,
                                        [TextMessage(text="Не смог найти лицо на изображении")])
                else:
                    unknown_encoding = face_enc[0]
                    for f in os.listdir(image_dir):
                        known_image = face_recognition.load_image_file(os.path.join(image_dir, f))
                        biden_encoding = face_recognition.face_encodings(known_image)[0]
                        results = face_recognition.compare_faces([biden_encoding], unknown_encoding)
                        print(results)
        # viber.send_messages(viber_request.sender.id, [message])
    elif isinstance(viber_request, ViberConversationStartedRequest) \
            or isinstance(viber_request, ViberSubscribedRequest) \
            or isinstance(viber_request, ViberUnsubscribedRequest):
        viber.send_messages(viber_request.sender.id, [
            TextMessage(None, None, viber_request.get_event_type())
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn(
            "client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)


def set_webhook(viber):
    viber.set_webhook('https://46f7b12b.ngrok.io/')


if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(5, 1, set_webhook, (viber,))
    t = threading.Thread(target=scheduler.run)
    t.start()

    # context = ('server.crt', 'server.key')
    app.run(port=3000, debug=True)
