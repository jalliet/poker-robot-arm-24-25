# import the InferencePipeline interface
from inference import InferencePipeline
# import a built in sink called render_boxes (sinks are the logic that happens after inference)
from inference.core.interfaces.stream.sinks import render_boxes
from inference.core.interfaces.camera.entities import VideoFrame
import cv2
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Custom sink function to handle predictions
def my_custom_sink(predictions: dict, video_frame: VideoFrame):
    
    # Iterate through each prediction in the predictions list
    for p in predictions['predictions']:
        center_x = p['x']
        center_y = p['y']
        print(f"Hand detected at x: {center_x}, y: {center_y}")

# New function to call both render_boxes and my_custom_sink
def combined_sink(predictions: dict, video_frame: VideoFrame):
    render_boxes(predictions, video_frame)
    my_custom_sink(predictions, video_frame)

# create an inference pipeline object
pipeline = InferencePipeline.init(
    model_id="hand_detect-xhlhk/2", # set the model id to a yolov8x model with in put size 1280
    video_reference=0, # set the video reference (source of video), it can be a link/path to a video file, an RTSP stream url, or an integer representing a device id (usually 0 for built in webcams)
    on_prediction=combined_sink, # use the combined sink function
    api_key=os.getenv("INFERENCE_API_KEY"), # provide your roboflow api key for loading models from the roboflow api
)
# start the pipeline
pipeline.start()
# wait for the pipeline to finish
pipeline.join()