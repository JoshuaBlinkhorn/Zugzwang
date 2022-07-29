#!/usr/bin/env python

from setuptools import setup

setup(
   name='zugzwang',
   version='1.0',
   description='Spaced repetition chess training',
   author='Joshua Blinkhorn',
   author_email='joshuablinkhorn@hotmail.co.uk',
   packages=['zugzwang'],  #same as name
   install_requires=['wheel', 'chess',], #external packages as dependencies
)
