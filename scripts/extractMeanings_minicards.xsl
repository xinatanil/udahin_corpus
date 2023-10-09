<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:saxon="http://saxon.sf.net/"
    xmlns:foo="http://whatever"
    version="2.0">
    <xsl:strip-space elements="*"/>
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="text()"/>
    <xsl:template match="/root">
    <root>
      <xsl:text>&#xa;</xsl:text>
      <xsl:copy-of select="card[not(homonym) and meaning and descendant::*[contains(., ':')]]"/>
    </root>
    </xsl:template>
    
</xsl:stylesheet>