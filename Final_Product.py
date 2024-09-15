import torch
import cv2
import os
from datetime import datetime
from b2sdk.v2 import B2Api
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore



# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5s.pt')
model.conf=0.45

# Set webcam capture
#cam="rtsp://192.168.1.3:8080/h264_pcm.sdp"
cam="http://192.168.137.159:8080/video"
cap = cv2.VideoCapture(cam)
#cam ="http://192.168.1.3:4747/video"
#cap = cv2.VideoCapture('Detect_Fire.mp4')

# Fetch the service account key JSON file contents
cred = credentials.Certificate("service.json")

# Initialize the Firebase app with the service account key
firebase_admin.initialize_app(cred)

# Get a reference to the Firestore client
db = firestore.client()

# Define the document reference
doc_ref = db.collection('users').document('z14weH9UYcMknKhBiKs1U0lHEI92')


# Set video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
filename='NONAME'
#width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
writer = cv2.VideoWriter()

# Set up backblaze storage API
b2 = B2Api()
b2.authorize_account(realm="production",application_key_id="005e8b38869c3170000000001", application_key="K005Bl3gPBvOH3KIRPLVSL3wPSNa5Ko")

# Send the JSON object to the backend server using an HTTP POST request
# Set Backblaze B2 bucket
#bucket_name = "Firetest"
#bucket = b2.get_bucket_by_name(bucket_name)

# Loop through webcam frames
while True:
    # Capture frame
    ret, frame = cap.read()
    if not ret:
        break
    # Convert frame to RGB and resize
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (640, 640))
    
    # Detect objects in frame using YOLOv5
    results = model(frame)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    class_name='Not'

        # Draw bounding boxes around the detected objects
    for result in results.pred:
        for det in result:
            x1, y1, x2, y2, conf, cls = det.tolist()
            label = f'{model.names[cls]} {conf:.2f}'
            class_name=model.names[cls]
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (60, 20, 220), 2)
            cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,228,225), 2)
    
    # Display frame
    cv2.imshow('Webcam', frame)    

    # Write frame to video
    if class_name =='Fire':
        if not writer.isOpened():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            timestring = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            filename = f'Detection_{timestamp}.mp4'
            # Append new data to the Firestore document
            #timestring = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data_Time=[timestring]
            doc_ref.update({'Time': firestore.ArrayUnion(new_data_Time)})
            new_data_type_detect = ['Fire']
            doc_ref.update({'typeDetect': firestore.ArrayUnion(new_data_type_detect)})
            new_data_camera_name=['Camera 1']
            doc_ref.update({'cameraName': firestore.ArrayUnion(new_data_camera_name)})

            #print("UP",filename)
            writer.open(filename, fourcc, 30, (640, 640), True)
        writer.write(frame)
    else :
        writer.release()
        #print("DOWN",filename)
        if os.path.exists(filename):
                    # Upload output video to backblaze storage and print URL
                    bucket = b2.get_bucket_by_name("FinalProduct")
                    bucket.upload_local_file(filename,filename)
                    url = bucket.get_download_url(filename)
                    print(f'Uploaded video to Backblaze B2: {url}')
                    filename ='NONAME'
                    # Append new data to the Firestore document
                    new_data_Location = ['First Floor']
                    doc_ref.update({'Location': firestore.ArrayUnion(new_data_Location)})
                    new_data_url_video=[url]
                    doc_ref.update({'detectURL': firestore.ArrayUnion(new_data_url_video)})


    # Check for key press
    key = cv2.waitKey(1)
    if key == 27: # ESC key to quit
        break

# Release video writer and webcam capture
#writer.release()
cap.release()
cv2.destroyAllWindows()

