import cv2
import sys
from pypylon import pylon

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

if __name__ == '__main__':
    # Set up tracker.
    tracker_types = ['BOOSTING', 'MIL', 'KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']
    tracker_type = tracker_types[1]

    if int(minor_ver) < 3:
        tracker = cv2.Tracker_create(tracker_type)
    else:
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        elif tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        elif tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        elif tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        elif tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        elif tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
        elif tracker_type == 'MOSSE':
            tracker = cv2.TrackerMOSSE_create()
        elif tracker_type == "CSRT":
            tracker = cv2.TrackerCSRT_create()

    # Set up Basler camera
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    # Check if camera is opened
    if not camera.IsOpen():
        print("Could not open camera")
        sys.exit()

    # Set the grab loop timeout policy
    camera.GrabLoopThreadUseTimeout.SetValue(True)
    camera.GrabLoopThreadTimeout.SetValue(5000)
    # camera.TimeoutHandling.SetValue(pylon.TimeoutHandling_ThrowException)

    # Start grabbing
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    # Read first frame
    grabResult = pylon.GrabResult()
    # if not camera.RetrieveResult(5000, grabResult):
    #     print('Cannot read camera feed')
    #     sys.exit()

    # Define an initial bounding box
    bbox = (287, 23, 86, 320)

    # Initialize tracker with first frame and bounding box
    frame = grabResult.GetArray()
    ok = tracker.init(frame, bbox)

    while True:
        # Retrieve a new frame
        grabResult = pylon.GrabResult()
        if not camera.RetrieveResult(5000, grabResult):
            break

        # Convert the grabbed image to an OpenCV image
        frame = grabResult.GetArray()

        # Start timer
        timer = cv2.getTickCount()

        # Update tracker
        ok, bbox = tracker.update(frame)

        # Calculate Frames per second (FPS)
        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);

        # Draw bounding box
        if ok:
            # Tracking success
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
        else:
            # Tracking failure
            cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

        # Display tracker type on frame
        cv2.putText(frame, tracker_type + " Tracker", (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

        # Display FPS on frame
        cv2.putText(frame, "FPS : " + str(int(fps)), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

        # Display result
        cv2.imshow("Tracking", frame)

        # Exit if ESC pressed
        k = cv2.waitKey(1) & 0xff
        if k == 27:
            break

    camera.StopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()