from distutils.core import setup
setup(
  name = 'pyHoops',         # How you named your package folder
  packages = ['pyHoops'],   # Chose the same as "name"
  version = '1.4',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'a python package for advanced basket data analytics',   # Give a short description about your library
  author = 'alessandroBombelli',                   # Type in your name
  author_email = 'alessandro.bombelli.87@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/alessandroBombelli/pyHoops',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/alessandroBombelli/pyHoops/releases/tag/v_01',    # I explain this later on
  keywords = ['DATA ANALYTICS', 'WEB-PARSING', 'BASKETBALL'],   # Keywords that define your package best
  install_requires=[
          'numpy',
          'matplotlib'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 2.7',      #Specify which python versions that you want to support
    'Programming Language :: Python :: 3.7'
  ],
)
