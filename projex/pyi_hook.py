""" Defines the hook required for the PyInstaller to use projex with it. """

import os
import projex.pyi

hiddenimports, datas = projex.pyi.collect(os.path.dirname(__file__))
hiddenimports.append('smtplib')