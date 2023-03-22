import os
# assign directory
directory = "unfilteredFiles"

for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):

        # filename = input("Enter filename")
        filename =f
        newFileName = filename+"NEW"
        lines = []

        with open(filename,'r') as oldFile:
            lines = oldFile.readlines()


        with open(newFileName, 'w') as newFile:
            for i,line in enumerate(lines):
                if "LiveBPM" in line or i == 0:
                    newFile.write(line)



