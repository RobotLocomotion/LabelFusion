"""
Usage:
    drake-visualizer --script testRegistration.py
"""
import corl.registration
from corl.registration import GlobalRegistration


globalRegistration = GlobalRegistration(view)
globalRegistration.testSuperPCS4()