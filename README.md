# AndroidVector

Stop exporting dozens of PNGs for your Android app -- this extension adds a new **save as** type for Android vector images.  Once installed, select **save as** or **save a copy**, and you should see a type called **Android VectorDrawable (\*.xml)** in the dropdown list.

### License

Copyright (C) 2017 [Owen Tosh](owen@owentosh.com)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see [gnu.org/licenses](http://www.gnu.org/licenses/).

### Installation

Copy the files `androidvector.py` and `androidvector.imx` to your extensions directory.  Reload Inkscape, and the new save type should be available.

### Usage and Limitations

- Currently, this extension only works with paths and groups.  All other objects will need to be converted to paths before saving the document; otherwise, they will not be represented in the vector image.
- Android vectors do not support gradients.  The extension will attempt to use one of the gradient colors instead.
- Android vectors have slightly different opacity implementations.  Inkscape has three opacity values for paths: stroke, fill, and overall.  Android has no overall opacity, so this is combined with the stroke and fill opacities.
- Android Studio has a function to reformat code.  If you need to modify any attributes in Android Studio, you can reformat the XML to make things easier on yourself.

### Change Log

#### 2017-02-14

- Scientific notation does not work in certain versions of Android.  Updated to resize the viewbox, and eliminate very small values (e.g. `8.675309e-17` becomes `0.0`).

#### 2017-01-06

- Initial version

### Improvements

- Currently only supports saving the entire document.  Would be helpful to migrate this extension to a more export-like tool, which would allow for exporting just a selection.
- Currently only supports groups and paths.  Would be helpful to automatically attempt to convert objects to paths before processing.
- XML formatting isn't the greatest.  Would be helpful to add newlines and spaces between tag attributes.