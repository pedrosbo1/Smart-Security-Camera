from socket import *
import time
import cv2
import sys
from mail import sendEmail
from flask import Flask, render_template, Response
from camera import VideoCamera
from flask_basicauth import BasicAuth
import time
import threading

#configuration server
serverName = '192.168.15.15'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

email_update_interval = 1 # sends an email only once in this time interval
video_camera = VideoCamera(flip=True) # creates a camera object, flip vertically
object_classifier = cv2.CascadeClassifier("models/facial_recognition_model.xml") # an opencv classifier

# App Globals (do not edit)
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'admin'
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)
last_epoch = 0

def Send_by_socket(bytesLidos):
    print "entrou"
    #bytesLidos = image.read() #le os bytes
    print "2"
    tamanhoArquivo = len(bytesLidos) #calcula o numero de bytes
    print "3"
    clientSocket.send(str(tamanhoArquivo).encode()) #envia o tamanho do arquivo
    print "4"
    resposta = clientSocket.recv(1024) #recebe uma resposta
    print ('From Server:', resposta.decode())
    clientSocket.send(bytesLidos) #envia os bytes lidos
    print('enviei arquivo')
    resposta = clientSocket.recv(1024) #recebe uma resposta apos o envio de arquivo
    print ('From Server:', resposta.decode()) 
    #clientSocket.close()

def check_for_objects():
	global last_epoch
	while True:
		try:
			frame, found_obj = video_camera.get_object(object_classifier)
			#print "teste"
			if found_obj and (time.time() - last_epoch) > email_update_interval:
				last_epoch = time.time()
				print "Sending email..."
				#sendEmail(frame)
				Send_by_socket(frame)
				print "done!"
		except:
			print "Error sending email: ", sys.exc_info()[0]
			
			

@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    t = threading.Thread(target=check_for_objects, args=())
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug=False)
    


