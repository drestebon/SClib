CC = gcc
CCOPTS = -Wall -O2 -ffast-math -fPIC -g

# Do not change these:
LIBS    = -lm
INCLUDE = -I/usr/include
LDFLAGS = -L/usr/lib 
LIB_DIR = ../lib
SRC_DIR = ../src

all:
	echo "FUMA 1"

.PHONY: clean
clean:
	rm -rf *.so *.o $(LIB_DIR)/*.so

#####################################################################
# Workers
#####################################################################
$(LIB_DIR)/%.so: $(SRC_DIR)/%.o
	$(CC) -shared -Wl,-soname,$@ -o $@ $<

%.o: %.c
	$(CC) $(INCLUDE) -c $(CCOPTS) $< $(LIBS)

