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
    <!-- Add check for empty <pos></pos> tags -->
    <!-- Add check for cards that have only <sameas> or <look> tags -->
    <xsl:template match="/root">
        <root>
            <xsl:text>&#xa;</xsl:text>
            <xsl:for-each select="card">
                <xsl:variable name="word" select="k"/>

                <xsl:variable name="homonymCount" select="count(descendant::homonym)"/>
                <xsl:variable name="meaningCount" select="count(descendant::meaning)"/>
                <xsl:variable name="exCount" select="count(descendant::ex)"/>
                <xsl:variable name="trnCount" select="count(descendant::trn)"/>
                <xsl:variable name="posCount" select="count(descendant::pos)"/>

                <xsl:choose>
                    <xsl:when test="$homonymCount = 0 and $meaningCount = 0 and $exCount = 0 and $trnCount = 0 and $posCount = 0">
                        <!-- <xsl:copy-of select="."/>
                        <xsl:text>&#xa;</xsl:text> -->
                    </xsl:when>
                    <xsl:when test="$posCount = 0">
                        <xsl:copy-of select="$word"/>
                        <xsl:text>&#xa;</xsl:text>
                    </xsl:when>
                </xsl:choose>
            </xsl:for-each>
        </root>
    </xsl:template>
</xsl:stylesheet>