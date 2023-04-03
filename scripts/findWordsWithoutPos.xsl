<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:saxon="http://saxon.sf.net/"
    xmlns:foo="http://whatever"
    version="2.0">
    <xsl:strip-space elements="*" />
    <xsl:output method="xml" indent="yes" />
    
    <xsl:template match="text()" />    
    <!-- Add check for empty <pos></pos> tags -->
    <!-- Add check for cards that have only <sameas> or <look> tags -->
    <xsl:template match="/root">
        <root>
            <xsl:text>&#xa;</xsl:text>
            <xsl:for-each select="card">
                <xsl:variable name="word" select="k"/>
                <xsl:variable name="posCount" select="count(descendant::pos)"/>
                <xsl:if test="$posCount = 0">
                    <xsl:value-of select="$word" />
                    <xsl:text>&#xa;</xsl:text>
                </xsl:if>
            </xsl:for-each>
        </root>
    </xsl:template>    
</xsl:stylesheet>
