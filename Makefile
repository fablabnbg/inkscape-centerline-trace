#
#
#
#######################################
APP	= inkscape-centerline-trace.py
TEST_INPUT_FILE = testdata-input.txt
TEST_OUTPUT_DIR = testdata-output
TEST_OUTPUT_LOG = testdata-output.log

#######################################
all:	test

clean:	

cleanall:	clean cleantest

#######################################
cleantest:
	@if [ -d $(TEST_OUTPUT_DIR) ]; then 	\
		echo "# Delete test output dir: <$(TEST_OUTPUT_DIR)>"; \
		rm -rf  $(TEST_OUTPUT_DIR) ;		\
	fi
	rm -f $(TEST_OUTPUT_LOG)

#######################################
test:
	@(echo "########################################";	\
	echo "### TEST: $(APP)";			\
	echo "########################################";	\
	echo "### git describe --all --long";		\
	git describe --all --long;			\
	echo "### git status -s";				\
	git status -s; 						\
	echo "########################################";	\
	if [ ! -d $(TEST_OUTPUT_DIR) ]; then 	\
		echo "# Create test output dir: <$(TEST_OUTPUT_DIR)>"; \
		mkdir -p $(TEST_OUTPUT_DIR) ;		\
		else								\
		echo "# Use test output dir: <$(TEST_OUTPUT_DIR)>"; \
	fi;										\
	echo "########################################";	\
	printf "### START TEST\n\n";					\
	for t in $$(cat $(TEST_INPUT_FILE)); do \
		seq=$$((seq+1));					\
		td=$$(dirname $$t);					\
		tod=$(TEST_OUTPUT_DIR)/$$td;		\
		tof=$(TEST_OUTPUT_DIR)/$$t;			\
		cmd="./$(APP) $$t > $$tof.svg";		\
		echo "########################################";	\
		printf "### TEST[%03d] start\n" $$seq; 	\
		printf "cmd: %s\n" "$$cmd";				\
		if [ ! -d $$tod ]; then 			\
			echo "# Create test output dir: <$$tod>"; \
			mkdir -p $$tod ;				\
		fi;									\
		eval "$$cmd";						\
		printf "file: %s\n"				$$tof.svg;		\
		printf "size: %s\n" $$(stat -f"%z" $$tof.svg);	\
		printf "wc: %s\n" "$$(wc  $$tof.svg | gawk '{ NF-=1; print $0}' )";	\
		printf "sha1sum: %s\n" $$(sha1sum	$$tof.svg |cut -f1 -d' ');	\
		printf "### TEST[%03d] end\n\n" $$seq; 	\
	done )  | tee $(TEST_OUTPUT_LOG).tmp
	mv $(TEST_OUTPUT_LOG).tmp $(TEST_OUTPUT_LOG)

#######################################
