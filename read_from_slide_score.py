from  slide_score_api.slidescore import APIClient
from PIL import Image
import io
import numpy as np
import matplotlib.pyplot as plt
import requests

import pandas as pd




APITOKEN= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJOYW1lIjoiV2ltIEFQSSBhY2Nlc3MiLCJJRCI6IjQwIiwiVmVyc2lvbiI6IjEuMCIsIkNhbkNyZWF0ZVVwbG9hZEZvbGRlcnMiOiJGYWxzZSIsIkNhblVwbG9hZCI6IkZhbHNlIiwiQ2FuRG93bmxvYWRTbGlkZXMiOiJUcnVlIiwiQ2FuRGVsZXRlU2xpZGVzIjoiRmFsc2UiLCJDYW5VcGxvYWRPbmx5SW5Gb2xkZXJzIjoiIiwiQ2FuUmVhZE9ubHlTdHVkaWVzIjoiIiwiQ2FuTW9kaWZ5T25seVN0dWRpZXMiOiIiLCJDYW5HZXRDb25maWciOiJUcnVlIiwiQ2FuR2V0UGl4ZWxzIjoiVHJ1ZSIsIkNhblVwbG9hZFNjb3JlcyI6IkZhbHNlIiwiQ2FuQ3JlYXRlU3R1ZGllcyI6IkZhbHNlIiwiQ2FuUmVpbXBvcnRTdHVkaWVzIjoiRmFsc2UiLCJDYW5EZWxldGVPd25lZFN0dWRpZXMiOiJGYWxzZSIsIkNhbkdldFNjb3JlcyI6IlRydWUiLCJDYW5HZXRBbnlTY29yZXMiOiJUcnVlIiwibmJmIjoxNjE2NDkxNTE1LCJleHAiOjE2NDc5OTAwMDAsImlhdCI6MTYxNjQ5MTUxNX0.duMtd4ZHkyfDSEP2E5MHvnamggZutoCFuYuARn_M_xo"
# replace the URL and APITOKEN
api = APIClient('https://slidescore.angiogenesis-analytics.nl', APITOKEN)




# export results for a single slide
# TODO: change the IDs to the study/case/slide you want (see the URL), question is the EXACT text of the question, user is email
studyid = 2
question = None
user = "wim.zwart@angiogenesis-analytics.nl"
imageid = 474
caseid = 13

for r in api.get_results(studyid=studyid, question=question, email=user, imageid=imageid, caseid=caseid):
   print(r.toRow().split('\t'))
# export annotation into an XML format (this one is used by ASAP https://github.com/computationalpathologygroup/ASAP


response = api.perform_request("Scores", {"studyid": studyid, "question": question, "email": user, "imageid": None,
                                           "caseid": caseid})
rjson = response.json()


print("---_")
# print(rjson)
imgageIDs=set()
caseName=""
for r in rjson:
   if not len(caseName)>0:
      caseName = r['caseName']
   elif caseName != r['caseName']:
      print(f"inconsistent casename {r['caseName']}")

   imgageIDs.add(r['imageID'])

print("---_")

print(caseName, imgageIDs)

USE_ASAP=False
if USE_ASAP:
   question = 'anno2'
   print(api.export_ASAP(imageid, user, question))

# export screenshot for all images in a case





# for i in images:
#     if i["caseID"] == caseid:
#         api.get_screenshot_whole(i["id"], user, question, "screenshot" + str(i["id"]) + ".jpeg")


# images = api.get_images(studyid)
# df=pd.DataFrame()
# for image in images:
#     s=pd.Series(image)
#     df=df.append(s, ignore_index=True)
# df.to_html("images.html")


level=10

def get_tile(api, imageid, level,x,y):
   response = api.perform_request("GetTileServer?imageId=" + str(imageid), None, method="GET")
   rjson = response.json()
   cookie=  rjson['cookiePart']
   url= api.end_point.replace("/Api/", f"/i/{imageid}/{rjson['urlPart']}/i_files/{level}/{x}_{y}.jpeg")
   r = requests.get(url, cookies={'t': cookie})
   img = Image.open(io.BytesIO(r.content))
   return img


def get_metadata(api, imageid):
   response = api.perform_request("GetImageMetadata?imageId=" + str(imageid), None, method="GET")
   rjson = response.json()
   metadata=rjson['metadata']
   return metadata


def get_size(api, imageid):
   metadata=get_metadata(api, imageid)
   print(metadata)
   width=metadata['level0Width']
   height=metadata['level0Height']
   return width,height

def get_tile_size(api, imageid):
   metadata=get_metadata(api, imageid)
   tile_width=metadata['level0TileWidth']
   tile_height=metadata['level0TileHeight']
   return tile_width,tile_height


width,height= get_size(api, imageid)
tile_width,tile_height = get_tile_size(api, imageid)
max_level=max(width,height).bit_length()




print(width,height)
print(max_level)




zoom_level=5
rect=[[0,0],[14096,14096]]

zoom_level=1
rect=[[2,2],[512,512]]


zoom_level=4
rect=[[10000,10000],[14023,14103]]


x_from=int(rect[0][0]//(tile_width*2**zoom_level))
x_to=int((rect[1][0])//(tile_width*2**zoom_level))+1
y_from=int(rect[0][1]//(tile_height*2**zoom_level))
y_to=int((rect[1][1])//(tile_height*2**zoom_level))+1

img_width=(rect[1][0]-rect[0][0])//(2**zoom_level)+1
img_height=(rect[1][1]-rect[0][1])//(2**zoom_level)+1
img=np.zeros((img_height, img_width,3), dtype=np.uint8)


print(img_width,img_height)

response = api.perform_request("GetTileServer?imageId=" + str(imageid), None, method="GET")
rjson = response.json()
cookie = rjson['cookiePart']


verbose=False
first=True

for x in range (x_from, x_to):

   left_img = min(max((x * tile_width * 2 ** zoom_level - rect[0][0]) // (2 ** zoom_level), 0), img_width - 1)
   right_img = min(max((((x + 1) * tile_width - 1) * 2 ** zoom_level - rect[0][0]) // (2 ** zoom_level), 0),
                   img_width - 1)
   left_tile = (left_img + rect[0][0] // (2 ** zoom_level)) % tile_width
   right_tile = (right_img + rect[0][0] // (2 ** zoom_level)) % tile_width

   for y in range(y_from, y_to):

      url = api.end_point.replace("/Api/", f"/i/{imageid}/{rjson['urlPart']}/i_files/{max_level-zoom_level}/{x}_{y}.jpeg")
      if True:
         r = requests.get(url, cookies={'t': cookie})
      first = False
      tile = Image.open(io.BytesIO(r.content))
      tile = np.asarray(tile)
      top_img  = min(max((y*tile_height*2**zoom_level-rect[0][1])//(2**zoom_level),0),img_height-1)
      bottom_img = min(max((((y+1)*tile_height-1)*2**zoom_level-rect[0][1])//(2**zoom_level),0),img_height-1)
      top_tile = (top_img +rect[0][1]//(2**zoom_level))%tile_height
      bottom_tile = (bottom_img + rect[0][1]//(2**zoom_level))%tile_height
      if verbose:
         print(f"Left_image: {left_img}, Right_image {right_img} {2**zoom_level}")
         print(f"Left_tile: {left_tile}, Right_tile {right_tile}")
         print(f"Top_image: {top_img}, Bottom_image {bottom_img}")
         print(f"Top_tile: {top_tile}, Bottom_tile {bottom_tile}")

      img[top_img:bottom_img+1,left_img: right_img+1] = tile[top_tile:bottom_tile+1,left_tile: right_tile+1]




print("done")

#
plt.imshow(img)
plt.show()