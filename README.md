# Research-Project

## Current functionality:

This tool was designed to import and annotate videos to be used in the evaluation of real-world optical flow datasets. Currently, the tool supports the following functionatilies:

- Import of a video (.mp4, .avi, .mov)
- Selection of frames through a slider.
- Selection of frames via a timestamp input. Used for general. Most hollistic approach 
- Selection of frames via _Previous_ and _Next_ Buttons. Most granular approach.
- An offset input field, which shows how many many frames apart the two images are. By default, this is set to 1.
- The ability to zoom both images, such that pixels can be very clearly mapped and located between frames. 
- Selection of a pixel in one frame and mapping it to a corresponding pixel in the subsequent one
- Annotate multiple pixel pairs, with the maximum number specified by the user 
- Color-coded annotations for visual clarity 
- When a pixel is selected in the first frame, it is temporarily colored yellow. After selecting the corresponding pixel in the second frame, the pair is assigned a random color.
- Undo functionality for the most recent annotation
- Clear all existing annotations from the current frame pair
- AAnnotate multiple, different pairs of frames from the same video
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
- Allow users to click on a pixel in Frame 1, and then click on the corresponding mapped pixel in Frame 2. 
- Visually draw a dot pair showing the connection between the two.
- Allow undoing the most recent annotation. 
- Allow the user to specify the number of pairs they want to annotate.
- Each pair should have a unique color.
- Have an immediate feedback when selecting the point in the first frame by placing a marker on that spot, not only after the complete pair is selected.
- Store the list of annotations as pairs of coordinates.
- Add a method that allows me to import image pairs into this application, and have it function as a video was imported.
- Modify all methods to no longer require self.cap when handling the new import image function.
- Modify the code such that i can change the import type dynamically.




