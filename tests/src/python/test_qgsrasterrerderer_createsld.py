# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_qgsrasterrenderer_createsld.py
    ---------------------
    Date                 : December 2018
    Copyright            : (C) 2018 by Luigi Pirelli
    Email                : luipir at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *less
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Luigi Pirelli'
__date__ = 'December 2018'
__copyright__ = '(C) 2018, Luigi Pirelli'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import qgis  # NOQA

import os

from qgis.PyQt.QtCore import (
    Qt,
    QDir,
    QFile,
    QIODevice,
    QPointF,
    QSizeF,
    QFileInfo,
)
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtGui import QColor, QFont

from qgis.core import (
    QgsRasterLayer,
    QgsMultiBandColorRenderer,
    QgsContrastEnhancement,
    QgsRasterMinMaxOrigin,
    Qgis,
)
from qgis.testing import start_app, unittest
from utilities import unitTestDataPath

# Convenience instances in case you may need them
# not used in this test
start_app()
TEST_DATA_DIR = unitTestDataPath()


class TestQgsRasterRendererCreateSld(unittest.TestCase):

    """
     This class tests the creation of SLD from QGis raster layers
    """

    @classmethod
    def setUpClass(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def __init__(self, methodName):
        """Run once on class initialization."""
        unittest.TestCase.__init__(self, methodName)
        myPath = os.path.join(TEST_DATA_DIR, 'landsat.tif')
        rasterFileInfo = QFileInfo(myPath)
        self.raster_layer = QgsRasterLayer(rasterFileInfo.filePath(),
                                           rasterFileInfo.completeBaseName())

    def testMultiBandColorRenderer(self):
        rasterRenderer = QgsMultiBandColorRenderer(
            self.raster_layer.dataProvider(), 3, 1, 2)
        self.raster_layer.setRenderer(rasterRenderer)
        self.raster_layer.setContrastEnhancement( algorithm=QgsContrastEnhancement.StretchToMinimumMaximum,
                                                  limits=QgsRasterMinMaxOrigin.MinMax );

        dom, root = self.rendererToSld(self.raster_layer.renderer())
        self.assertOpacity(root, '1')
        self.assertChannelBand(root, 'sld:RedChannel', '3')
        self.assertChannelBand(root, 'sld:GreenChannel', '1')
        self.assertChannelBand(root, 'sld:BlueChannel', '2')
        # check gamma properties from [-100:0] streched to [0:1]
        #  and (0:100] stretche dto (1:100]
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '-100'})
        self.assertGamma(root, '0')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '-50'})
        self.assertGamma(root, '0.5')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '0'})
        self.assertGamma(root, '1')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '1'})
        self.assertGamma(root, '1')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '100'})
        self.assertGamma(root, '100')
        # input contrast are always integer, btw the value is managed also if it's double
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '1.1'})
        self.assertGamma(root, '1.1')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '1.6'})
        self.assertGamma(root, '1.6')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '-50.5'})
        self.assertGamma(root, '0.495')
        dom, root = self.rendererToSld(rasterRenderer, {'contrast': '-0.1'})
        self.assertGamma(root, '0.999')

    def testStretchingAlgorithm(self):
        rasterRenderer = QgsMultiBandColorRenderer(
            self.raster_layer.dataProvider(), 3, 1, 2)
        self.raster_layer.setRenderer(rasterRenderer)

        # check StretchToMinimumMaximum stretching alg
        self.raster_layer.setContrastEnhancement( algorithm=QgsContrastEnhancement.StretchToMinimumMaximum,
                                                  limits=QgsRasterMinMaxOrigin.MinMax );
        dom, root = self.rendererToSld(self.raster_layer.renderer())
        self.assertContrastEnhancement(root, 'sld:RedChannel', 'StretchToMinimumMaximum', '51', '172')
        self.assertContrastEnhancement(root, 'sld:GreenChannel', 'StretchToMinimumMaximum', '122', '130')
        self.assertContrastEnhancement(root, 'sld:BlueChannel', 'StretchToMinimumMaximum', '133', '148')

        # check StretchAndClipToMinimumMaximum stretching alg
        self.raster_layer.setContrastEnhancement( algorithm=QgsContrastEnhancement.StretchAndClipToMinimumMaximum,
                                                  limits=QgsRasterMinMaxOrigin.MinMax );
        dom, root = self.rendererToSld(self.raster_layer.renderer())
        self.assertContrastEnhancement(root, 'sld:RedChannel', 'ClipToZero', '51', '172')
        self.assertContrastEnhancement(root, 'sld:GreenChannel', 'ClipToZero', '122', '130')
        self.assertContrastEnhancement(root, 'sld:BlueChannel', 'ClipToZero', '133', '148')

        # check ClipToMinimumMaximum stretching alg
        self.raster_layer.setContrastEnhancement( algorithm=QgsContrastEnhancement.ClipToMinimumMaximum,
                                                  limits=QgsRasterMinMaxOrigin.MinMax );
        dom, root = self.rendererToSld(self.raster_layer.renderer())
        self.assertContrastEnhancement(root, 'sld:RedChannel', 'ClipToMinimumMaximum', '51', '172')
        self.assertContrastEnhancement(root, 'sld:GreenChannel', 'ClipToMinimumMaximum', '122', '130')
        self.assertContrastEnhancement(root, 'sld:BlueChannel', 'ClipToMinimumMaximum', '133', '148')

        # check NoEnhancement stretching alg
        self.raster_layer.setContrastEnhancement( algorithm=QgsContrastEnhancement.NoEnhancement );
        dom, root = self.rendererToSld(self.raster_layer.renderer())
        self.assertContrastEnhancement(root, 'sld:RedChannel')
        self.assertContrastEnhancement(root, 'sld:GreenChannel')
        self.assertContrastEnhancement(root, 'sld:BlueChannel')

    def assertGamma(self, root, expectedValue, index=0):
        enhancement = root.elementsByTagName('sld:ContrastEnhancement').item(index)
        gamma = enhancement.firstChildElement( 'sld:GammaValue' )
        self.assertEqual(expectedValue, gamma.firstChild().nodeValue())

    def assertOpacity(self, root, expectedValue, index=0):
        opacity = root.elementsByTagName('sld:Opacity').item(index)
        self.assertEqual(expectedValue, opacity.firstChild().nodeValue())

    def assertContrastEnhancement(self, root, bandTag, expectedAlg=None, expectedMin=None, expectedMax=None, index=0):
        channelSelection = root.elementsByTagName('sld:ChannelSelection').item(index)
        self.assertIsNotNone(channelSelection)
        band = channelSelection.firstChildElement( bandTag )
        # check if no enhancement alg is iset
        if ( not expectedAlg ):
            contrastEnhancementName = band.firstChildElement('sld:ContrastEnhancement')
            self.assertEqual('', contrastEnhancementName.firstChild().nodeName())
            return
        # check if enhancement alg is set
        contrastEnhancementName = band.firstChildElement('sld:ContrastEnhancement')
        self.assertEqual('Normalize', contrastEnhancementName.firstChild().nodeName())
        normalize = contrastEnhancementName.firstChildElement( 'Normalize' )
        vendorOptions = normalize.elementsByTagName('VendorOption')
        for vendorOptionIndex in range(vendorOptions.count()):
            vendorOption = vendorOptions.at(vendorOptionIndex)
            self.assertEqual('VendorOption', vendorOption.nodeName())
            if ( vendorOption.attributes().namedItem('name').nodeValue() == 'algorithm'):
                self.assertEqual(expectedAlg, vendorOption.firstChild().nodeValue())
            elif (vendorOption.attributes().namedItem('name').nodeValue() == 'minValue'):
                self.assertEqual(expectedMin, vendorOption.firstChild().nodeValue())
            elif (vendorOption.attributes().namedItem('name').nodeValue() == 'maxValue'):
                self.assertEqual(expectedMax, vendorOption.firstChild().nodeValue())
            else:
                self.fail('Unrecognised vendorOption name {}'.format(vendorOption.attributes().namedItem('name').nodeValue()) )

    def assertChannelBand(self, root, bandTag, expectedValue, index=0):
        channelSelection = root.elementsByTagName('sld:ChannelSelection').item(index)
        self.assertIsNotNone(channelSelection)
        band = channelSelection.firstChildElement( bandTag )
        sourceChannelName = band.firstChildElement('sld:SourceChannelName')
        self.assertEqual(expectedValue, sourceChannelName.firstChild().nodeValue())

    def rendererToSld(self, renderer, properties={}):
        dom = QDomDocument()
        root = dom.createElement("FakeRoot")
        dom.appendChild(root)
        renderer.toSld(dom, root, properties)
        return dom, root


if __name__ == '__main__':
    unittest.main()
