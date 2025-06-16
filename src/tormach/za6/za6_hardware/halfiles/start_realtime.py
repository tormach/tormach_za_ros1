from hal_hw_interface import hal

# Make sure the realtime runtime is started only after whole configuration
# is loaded and not sooner

hal.start_threads()
