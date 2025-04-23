# Research-Project

## Current functionality:

This tool was designed to import and annotate videos to be used in the evaluation of real-world optical flow datasets. Currently, the tool supports the following functionatilies:

- Import of a video (.mp4, .avi, .mov)
- Selection of frames through a slider.
- Selection of frames via a timestamp input. Used for general. Most hollistic approach 
- Selection of frames via _Previous_ and _Next_ Buttons. Most granular approach.
- An offset input field, which shows how many many frames apart the two images are. By default, this is set to 1.
- The ability to pan and zoom both images, such that pixels can be very clearly mapped and located between frames.

The tool is yet to implement the following:
- The ability to select a pixel from one frame, and map it to another
- The ability to export the resultant sparse vector field in a form understandable or comparable with the current model outputs. 


## Prompts used

A portion of this tool was using with the assistance of artifical intelligence and LLMs. To ensure transparency, all prompts used, alongside the models they were used on, are listed below:

### List of Prompts 
#### ChatGPT: Model ChatGPT-4-turbo
- Generate a tool in python that can take video inputs and display two frames of the video next to each other.
- Provide a GUI interface that allows me to slide across the video's time and displays the frame numbers
- Present a similar GUI using PyQT
- Modify the screen such that there is one slider for the starting, and it shows two consecutive frames instead. Additionally, add buttons for fine grained control. Finally, only show the slider once the video has been imported.
- Modify the script to now have an offset input for the user. This will then show frames with this offset i,e frames 1 and 3 for an offset of 2. An offset of 0 will show identical frames, so make this offset have a lower bound of 1. Additionally, make the application scale with window size, to allow for more fine grained viewing.
- Modify the application to be of a fixed size, and instead allow for zooming and panning the loaded images.
- Modify the application to now: Show frame numbers above the images. Resize the image boxes to fit the image aspect ratio. Change the layout to now have the images at the very bottom. The application should now show the load video button, and a corresponding text to show the file path of the imported video, followed by the slider, followed by the previous and next buttons, followed by the frame numbers, and finally the frames themselves, in resized boxes that fit the aspect ratio.
- Both options of: Annotating pixels in Frame 1 and mapping to Frame 2 and Exporting that pixel-pixel mapping as a vector field (e.g., JSON or numpy format) are future wants for the application. Write a prompt for any general purpose model that, when given the most recent iteration of code, can implement those features.
- Modify this text to be in paragraphs, such that it can be easily copied and stored in a text file.
- Modify the application again to now provide a box where a desired timestamp can be input. The application will then load the first frame of that timestamp, rounded to the closest second. This will also automatically update when the slider is moved, as well as automatically updating the slider itself when a time is selected. This input should only take effect once the user stops editing the input box.
- Change the layout such that the previous, next, and offset are on a seperate line than the slider and input field. Additionally, make it such that the offset is found between the previous and next buttons. Finally, make the application's theme match the system theme.


### Future Updates: LLM Prompt

In the list of prompts, I also asked ChatGPT-4-turbo to present a prompt that, when fed into any general purpose LLM, alongside the code, would implement the remaining features. Its response is as follows:

You are working with a PyQt5 GUI application that:

Loads and displays two video frames side-by-side.

Allows zooming and panning.

Shows frame numbers.

Lets users set a frame offset and navigate frames.

Keeps all UI elements in a structured layout.

You are provided with the full code of the application. Your task is to extend it with the following features:

New Features to Implement
1. Pixel Annotation and Mapping
Allow users to click on a pixel in Frame 1, and then click on the corresponding mapped pixel in Frame 2.

Visually draw a line or dot pair showing the connection between the two.

Allow undoing the most recent annotation.

Optional: Add basic color-coded markers or small tooltips for annotation IDs.

2. Annotation Storage
Store the list of annotations as pairs of coordinates:

python
Copy
Edit
annotations = [
    {'frame1': (x1, y1), 'frame2': (x2, y2)},
    ...
]
3. Export Functionality
Add a "Save Vector Field" button that exports the annotations to:

A JSON file (vector_field.json).

Optionally a .npy file with NumPy arrays if NumPy is available.

4. Visual Feedback and Usability
Make sure the UI updates correctly after each annotation.

Do not break zoom and pan functionality.

If the user switches frames, either persist the annotation view or clear it (you decide based on UX tradeoff and explain the choice).

Constraints
The app is currently structured with ZoomPanGraphicsView widgets for both frames.

The layout has a fixed size; images scale with zoom.

You must not break existing functionality.

Deliverables
Updated Python code.

Short explanation of where each new part was added.

(Optional) Suggestions for improving annotation UX further.