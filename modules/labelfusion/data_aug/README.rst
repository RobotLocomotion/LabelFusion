=====
Dependencies
=====

PIL, TensorFlow, Keras

=====
Instructions
=====

~In directorPython terminal

1. from labelfusion.data_aug import augmentData as augment
2. generator = augment.DataAugmentation()
3. generator.augmentWithKeras("logs/moving-camera")

This will add batches of randomly augmented data to the images folder in the log

see code for details on parameters for augmenting data

