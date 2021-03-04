*uhm*
=====

Author: Adam Moss

Installation: ``pip install uhm``

---

#### Remove uhm's and other filler words from videos. 

In the example below, the code detects 8 uhm's, at 6.22, 12.89, 44.81, 111.89, 136.37, 156.99, 165.11, and 172.22 seconds.  

[![IMAGE ALT TEXT](http://img.youtube.com/vi/NYk-2VHj9N0/0.jpg)](http://www.youtube.com/watch?v=NYk-2VHj9N0 "Original Video")

They have been automatically removed in the following video.

[![IMAGE ALT TEXT](http://img.youtube.com/vi/Yt0_rVvt7mo/0.jpg)](http://www.youtube.com/watch?v=Yt0_rVvt7mo "Video after de-uhming")

Usage
-----

You will need to set ``WATSON_API_KEY`` and ``WATSON_API_URL`` as environment variables. Alternatively these can be passed in

``dehm "in.mp4" "out.mp4" --api_key=<WATSON_API_KEY> --api_url=<WATSON_API_URL> ``
