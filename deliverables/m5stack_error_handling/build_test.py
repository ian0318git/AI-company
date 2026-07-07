#!/usr/bin/env python3
"""
Build script for test_error_handling.
Runs g++ with the proper flags via subprocess.
"""
import subprocess
import sys
import os

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

CXX = "g++"
FLAGS = [
    "-std=c++20",
    "-I.",
    "-Wall",
    "-Werror",
    "-Wno-unused-function",
    "-Wno-unused-variable",
    "-Wno-unused-parameter",
    "-Wno-volatile",
    "-Wno-class-memaccess",
    "-Wno-sign-compare",
]

print("=== Compiling error_handling.cpp ===")
r1 = subprocess.run([CXX, *FLAGS, "-c", "error_handling.cpp", "-o", "error_handling.o"],
                     capture_output=True, text=True)
if r1.returncode != 0:
    print("STDERR:", r1.stderr)
    print("STDOUT:", r1.stdout)
    sys.exit(r1.returncode)
print("OK")

print("=== Compiling test_error_handling.cpp ===")
r2 = subprocess.run([CXX, *FLAGS, "-c", "test_error_handling.cpp", "-o", "test_error_handling.o"],
                     capture_output=True, text=True)
if r2.returncode != 0:
    print("STDERR:", r2.stderr)
    print("STDOUT:", r2.stdout)
    sys.exit(r2.returncode)
print("OK")

print("=== Linking ===")
r3 = subprocess.run([CXX, *FLAGS, "test_error_handling.o", "error_handling.o",
                      "-o", "test_error_handling"],
                     capture_output=True, text=True)
if r3.returncode != 0:
    print("STDERR:", r3.stderr)
    print("STDOUT:", r3.stdout)
    sys.exit(r3.returncode)
print("OK - binary: test_error_handling")

print("\n=== Running tests ===")
r4 = subprocess.run(["./test_error_handling"], capture_output=True, text=True)
print(r4.stdout)
if r4.stderr:
    print("STDERR:", r4.stderr)
print(f"Exit code: {r4.returncode}")
sys.exit(r4.returncode)
