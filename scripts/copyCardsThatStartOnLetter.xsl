<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:strip-space elements="*"/>
  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="text()"/>

  <xsl:key name="elements" match="*" use="name()"/>

  <xsl:template match="/root">
    <root>
      <xsl:text>&#xa;</xsl:text>
      <xsl:for-each select="card">
        <xsl:variable name="word" select="k"/>
        <xsl:if test="starts-with($word, 'э')">
          <xsl:copy-of select="."/>
          <xsl:text>&#xa;</xsl:text>
        </xsl:if>
      </xsl:for-each>
    </root>
  </xsl:template>

</xsl:stylesheet>