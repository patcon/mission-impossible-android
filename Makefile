
clean:
	@echo "Clean the python virtualenv, distribution and package folders/files."
	rm -rf bin build dist include lib lib64 *.egg-info


clean-py:
	@echo "Clean the byte-compiled, optimized or DLL files."
	find . -name __pycache__ | xargs -i rm -rf {}
	find . -name '*.py[cod]' | xargs -i rm -rf {}


clean-all: clean clean-py
	@echo "Clean all, including the workspace folders/files."
	rm -rf builds resources definitions


define INFOTEXT
---
A Python3 virtual environment has been created. You can activate it using:
  $$ source bin/activate

To exit out of the virtual environment just call the `deactivate` function:
  $$ deactivate

Once inside the virtual environment make sure to check the README.md file.
endef
export INFOTEXT

prepare: clean
	@echo "Creating a python3 virtual environment..."
	virtualenv -p python3 .
	@echo "$$INFOTEXT"
