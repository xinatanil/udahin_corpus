<?xml version="1.0"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="utf-8" indent="yes" omit-xml-declaration="no"/>
  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/root">
    <root>
      <xsl:for-each select="card">
        <xsl:sort select="upper-case(k)" lang="ru"/>
        <xsl:copy-of select="."/>
      </xsl:for-each>
    </root>
  </xsl:template>
</xsl:stylesheet>
