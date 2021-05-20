from urllib.request import urlopen
from tempfile import NamedTemporaryFile
import platform

# This is just to make sure that the systems path is set up correctly, to have correct imports.
# (It can be ignored)

from flowcontrol.utils.misc import query_yes_no

from zipfile import ZipFile

import os


if __name__ == "__main__":

	jar_file = "vadere-server.jar"

	if platform.system() == "Linux":
		zipurl = "http://www.vadere.org/builds/master/vadere.master.linux.zip"
	elif platform.system()== "Windows":
		zipurl = "http://www.vadere.org/builds/master/vadere.master.windows.zip"
	else:
		raise SystemError("Linux or Windows system required.")

	file_path = os.path.dirname(os.path.abspath(__file__))

	jar_file_path = os.path.join( file_path, jar_file )

	is_download = True
	if os.path.isfile(jar_file_path):
		print(f"*.jar file found: {file_path}/{jar_file}.")
		is_download = False
		if query_yes_no("Use existing *.jar file [Y] or download latest [n]?") == False:
			os.remove(jar_file_path)
			is_download = True

	if is_download:
		print(f"Download vadere-server.jar. Download link: {zipurl}")
		print("Download started .. (this can take a couple of minutes)")
		with urlopen(zipurl) as zipresp, NamedTemporaryFile() as tfile:
			tfile.write(zipresp.read())
			tfile.seek(0)

			# Create a ZipFile Object and load sample.zip in it
			with ZipFile(tfile.name, 'r') as zipObj:
				# Get a list of all archived file names from the zip
				listOfFileNames = zipObj.namelist()
				# Iterate over the file names
				for fileName in listOfFileNames:
					# Check filename endswith csv
					if fileName == jar_file:
						# Extract a single file from zip
						zipObj.extract(fileName, jar_file_path)

		print(".. download completed.")

