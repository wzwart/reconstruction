import slideio
import matplotlib.pyplot as plt

file_path= r".\downloaded\21411.svs"

slide = slideio.open_slide(file_path,"SVS")
scene = slide.get_scene(0)
print(scene.size)
print(scene.resolution)


pos_in_scene=[10000,10000]
size_in_scene=[1000,1000]
size_in_block=[1000,1000]

block= scene.read_block(rect=(pos_in_scene[0],pos_in_scene[0],pos_in_scene[0]+size_in_scene[0],pos_in_scene[1]+size_in_scene[1]), size=size_in_block)
print("data read")

print(type(scene))
print(block.shape)



plt.imshow(block)

plt.show()





