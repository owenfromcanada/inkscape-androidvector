#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exports the drawing as an XML appropriate for use as an Android VectorDrawable.

Copyright (C) 2017 Owen Tosh <owen@owentosh.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import lxml.etree as et

import inkex
import cubicsuperpath as csp
import simpletransform as st
import simplestyle as ss

inkex.localize()

def _ns(tag):
    """Add the Android namespace to a tag or attribute.
        
    Required arguments:
    tag -- string, tag or attribute
    """
    return '{%s}%s' % ('http://schemas.android.com/apk/res/android', tag)

class AndroidVector(inkex.Effect):
    """Main effect class."""
    
    def effect(self):
        """Convert the SVG to an Android Vector XML object."""
        # get inkscape root element
        svg = self.document.getroot()
        
        # initialize android root element
        vector = et.Element('vector')
        
        # handle root attributes
        vector.set(_ns('name'), svg.get('id', 'svgimage'))
        
        width = svg.get('width')
        height = svg.get('height')
        if width is None:
            inkex.errormsg(_('The document width attribute is missing.'))
            return
        if height is None:
            inkex.errormsg(_('The document height attribute is missing.'))
            return
        # width and height are the only attributes using non-user units in the vector tag
        vector.set(_ns('width'), str(self.uutounit(self.__unittouu(width), 'px')) + 'dp')
        vector.set(_ns('height'), str(self.uutounit(self.__unittouu(height), 'px')) + 'dp')
        
        view_box = svg.get('viewBox')
        if view_box is None:
            inkex.errormsg(_('The document viewBox attribute is missing.'))
            return
        view_box_split = view_box.split()
        if len(view_box_split) != 4:
            inkex.errormsg(_('The document viewBox attribute is not formatted correctly.'))
            return
        
        # determine scale factor
        view_width = float(view_box_split[2])
        view_height = float(view_box_split[3])
        scale_fact = 1000.0/max(view_width, view_height)
        # set scale (remove need for scientific notation)
        svg.set('transform', 'scale(%f %f)' % (scale_fact, scale_fact))
        
        vector.set(_ns('viewportWidth'), str(view_width * scale_fact))
        vector.set(_ns('viewportHeight'), str(view_height * scale_fact))
        
        # parse child elements
        self.unique_id = 0
        ancestors = [svg]
        for el in svg:
            tag = self._get_tag_name(el)
            # ignore root's incompatible children
            if tag == 'g' or tag == 'path':
                subel = self._parse_child(el, ancestors)
                if subel is not None:
                    vector.append(subel)
        
        # save element tree
        self.etree = et.ElementTree(vector)
    
    def output(self):
        """Write element tree to file."""
        self.etree.write(sys.stdout, pretty_print=True)
    
    def __unittouu(self, param):
        """Wrap inkex.unittouu for compatibility.
        
        Required arguments:
        param -- string, to parse
        """
        try:
            return inkex.unittouu(param)
        except AttributeError:
            return self.unittouu(param)
    
    def _get_tag_name(self, node):
        """Strip namespace from tag."""
        if '}' in node.tag:
            return node.tag.split('}', 1)[1]
        else:
            return node.tag
    
    def _parse_child(self, src, ancestors):
        """Recursively parse through child elements.
        
        Return an element (including all decendants).
        
        Required arguments:
        src -- Element, child element to parse
        ancestors -- list of Element, list of parent elements up to root
        """
        # check for compatible tag
        tag = self._get_tag_name(src)
        
        if tag == 'g':
            el_tag = 'group'
        elif tag == 'path':
            el_tag = 'path'
        else:
            return None
        
        # initialize android element
        el = et.Element(el_tag)
        
        # set name attribute
        name = src.get('id')
        if name is None:
            name = el_tag + str(self.unique_id)
            self.unique_id += 1
        el.set(_ns('name'), name)
        
        if tag == 'g':
            # parse child elements
            ancestors.append(src)
            for child in src:
                subel = self._parse_child(child, ancestors)
                if subel is not None:
                    el.append(subel)
            ancestors.pop()
            
        else:
            # path element
            
            # get path data
            d = src.get('d')
            if d is None:
                return None
            
            # apply all transforms (including all ancestors - i.e. "flatten")
            p = csp.parsePath(d)
            
            ancestors.append(src)
            for anc in reversed(ancestors):
                if 'transform' in anc.attrib:
                    transform = anc.get('transform')
                    t = st.parseTransform(transform)
                    st.applyTransformToPath(t, p)
            ancestors.pop()
            
            # remove very small numbers (i.e. scientific notation)
            for i in range(len(p)):
                for j in range(len(p[i])):
                    for k in range(len(p[i][j])):
                        for l in range(len(p[i][j][k])):
                            if 'e-' in str(p[i][j][k][l]).lower():
                                p[i][j][k][l] = 0.0;
            
            # save path data in vector element
            el.set(_ns('pathData'), csp.formatPath(p))
            
            # parse styles
            if 'style' not in src.attrib:
                # set some basic defaults
                el.set(_ns('strokeColor'), '#000000')
                el.set(_ns('strokeWidth'), '1')
                el.set(_ns('fillColor'), '#FFFFFF')
            else:
                style = ss.parseStyle(src.get('style'))
                
                # overall object opacity
                # - not supported in android - merged with other opacities later
                opacity = 1.0
                if 'opacity' in style:
                    opacity = float(style['opacity'])
                
                # fill styles
                if 'fill' in style:
                    color = self._get_color(style['fill'])
                    if color is not None:
                        el.set(_ns('fillColor'), color)
                
                if 'fill-opacity' in style or 'opacity' in style:
                    alpha = opacity
                    if 'fill-opacity' in style:
                        alpha *= float(style['fill-opacity'])
                    el.set(_ns('fillAlpha'), str(alpha))
                
                if 'fill-rule' in style:
                    if style['fill-rule'] == 'evenodd':
                        el.set(_ns('fillType'), 'evenOdd')
                    elif style['fill-rule'] == 'nonzero':
                        el.set(_ns('fillType'), 'nonZero')
                
                # stroke styles
                if 'stroke' in style:
                    color = self._get_color(style['stroke'])
                    if color is not None:
                        el.set(_ns('strokeColor'), color)
                
                if 'stroke-width' in style:
                    el.set(_ns('strokeWidth'), str(self.__unittouu(style['stroke-width'])))
                
                if 'stroke-opacity' in style or 'opacity' in style:
                    alpha = opacity
                    if 'stroke-opacity' in style:
                        alpha *= float(style['stroke-opacity'])
                    el.set(_ns('strokeAlpha'), str(alpha))
                
                if 'stroke-linecap' in style:
                    el.set(_ns('strokeLineCap'), style['stroke-linecap'])
                
                if 'stroke-linejoin' in style:
                    el.set(_ns('strokeLineJoin'), style['stroke-linejoin'])
                
                if 'stroke-miterlimit' in style:
                    el.set(_ns('strokeMiterLimit'), style['stroke-miterlimit'])
        
        return el
    
    def _get_color(self, color):
        """Retrieve and parse an inkscape color for use in android.
        
        Return a string "#RRGGBB", or None if not understood.  If inkscape color
        is a gradient, attempt to use one of the gradient colors.
        
        Required arguments:
        color -- string, inkscape color (from "style" attribute)
        """
        if color.startswith('#'):
            # already in the correct format
            return color
        elif color == 'none':
            # no color defined, transparent - we'll rely on the opacity attributes instead
            return None
        elif color.startswith('url(#') and color.endswith(')'):
            # parse ID to check for a gradient
            id = color[5:-1]
            if id.startswith('linearGradient') or id.startswith('radialGradient'):
                doc = self.document
                
                # find defined gradient
                prefix_terms = []
                prefix_terms.append(inkex.addNS('defs', 'svg'))
                prefix_terms.append('/')
                prefix_terms.append('*[@id=\'')
                prefix = ''.join(prefix_terms)
                suffix = '\']'
                gradient = doc.find(prefix + id + suffix)
                
                # get link to the other gradient definition (with the colors defined)
                link_attr = inkex.addNS('href', 'xlink')
                if gradient is None or link_attr not in gradient.attrib:
                    return None
                link_id = gradient.get(link_attr)
                if link_id.startswith('#'):
                    link_id = link_id[1:]
                
                # get stop element
                suffix_terms = []
                suffix_terms.append('\']/')
                suffix_terms.append(inkex.addNS('stop', 'svg'))
                suffix = ''.join(suffix_terms)
                stop = doc.find(prefix + link_id + suffix)
                
                # parse style attribute of stop element
                if stop is None or 'style' not in stop.attrib:
                    return None
                style = ss.parseStyle(stop.get('style'))
                
                if 'stop-color' not in style:
                    return None
                
                # recursively attempt to parse the found color
                return self._get_color(style['stop-color'])
        
        # color wasn't understood
        return None

if __name__ == "__main__":
    vector = AndroidVector()
    vector.affect()
