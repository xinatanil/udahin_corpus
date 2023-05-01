<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:strip-space elements="*"/>
  <xsl:output method="text"/>

  <xsl:template match="text()"/>

  <xsl:key name="elements" match="*" use="name()"/>

  <xsl:template match="/root">
    <root>
      <xsl:text>???</xsl:text>
      <xsl:text>&#xa;</xsl:text>

      <xsl:for-each select="card">
        <xsl:variable name="word" select="k"/>
        <xsl:copy-of select="$word"/>
        <xsl:text>&#xa;</xsl:text>

        <xsl:if test="position() mod 50 = 0">
          <xsl:text>&#xa;&#xa;</xsl:text>
          <xsl:text>???</xsl:text>
          <xsl:text>&#xa;</xsl:text>
        </xsl:if>

      </xsl:for-each>
    </root>
  </xsl:template>

</xsl:stylesheet>