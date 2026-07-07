# Makefile for M5Stack Error Handling unit tests (Linux host build)
#
# Builds and runs the test suite using doctest single-header and g++.
# No ESP-IDF / Xtensa toolchain required — the module's non-ESP32 branches
# are exercised.
#
# Usage:
#   make          # download doctest.h (if missing), build, run
#   make build    # just build
#   make run      # run the test binary
#   make clean    # remove build artifacts

CXX       := g++
CXXFLAGS  := -std=c++20 -I. -Wall -Werror -Wno-unused-function -Wno-volatile -Wno-class-memaccess -Wno-sign-compare
LDFLAGS   :=
TARGET    := test_error_handling

DOCTEST_H := doctest.h
DOCTEST_URL := https://raw.githubusercontent.com/doctest/doctest/master/doctest/doctest.h

SRCS      := test_error_handling.cpp error_handling.cpp
OBJS      := $(SRCS:.cpp=.o)

.PHONY: all build run clean doctest

all: $(DOCTEST_H) build
	@echo ""
	@echo "=== Running tests ==="
	./$(TARGET)

build: $(DOCTEST_H) $(TARGET)

run: $(TARGET)
	./$(TARGET)

$(DOCTEST_H):
	@echo "Downloading doctest single-header..."
	wget -O $@ $(DOCTEST_URL)

%.o: %.cpp $(DOCTEST_H) error_handling.h
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

clean:
	$(RM) $(OBJS) $(TARGET)
	@echo "Cleanup done.  (doctest.h kept; remove manually if desired)"
