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
    
    
    <xsl:template match="/root">
        <root>
            <xsl:for-each select="card">
                <xsl:choose>
                    <xsl:when test="blockquote[matches(., '^\w+-? I:?$')]">
                        <card>
                            <xsl:text>&#xa;</xsl:text>
                            <xsl:copy-of select="k" />
                            <xsl:for-each select="blockquote">
                                <xsl:variable name="tagContent" select="."/>
                                <xsl:choose>
                                    <xsl:when test='matches($tagContent, "^\w+-? I:?$")' >
                                        <xsl:text>&#xa;</xsl:text>
                                        <xsl:text>homonym</xsl:text>
                                        <xsl:text>&#xa;</xsl:text>
                                        <xsl:copy-of select="." />
                                    </xsl:when>
                                    <xsl:when test='
                                        matches($tagContent, "^\w+-? II:?$") or 
                                        matches($tagContent, "^\w+-? III:?$") or
                                        matches($tagContent, "^\w+-? IV:?$") or
                                        matches($tagContent, "^\w+-? V:?$") or
                                        matches($tagContent, "^\w+-? VI:?$") or
                                        matches($tagContent, "^\w+-? VII:?$")' >
                                        <xsl:text>&#xa;</xsl:text>
                                        <xsl:text>closingHomonym</xsl:text>
                                        <xsl:text>&#xa;</xsl:text>
                                        <xsl:text>homonym</xsl:text>
                                        <xsl:text>&#xa;</xsl:text>
                                        <xsl:copy-of select="." />
                                    </xsl:when>
                                    <xsl:when test="position() = last()" >
                                        <xsl:copy-of select="." />
                                        <xsl:text>&#xa;</xsl:text>
                                        <xsl:text>closingHomonym</xsl:text>
                                        <xsl:text>&#xa;</xsl:text>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:copy-of select="." />
                                    </xsl:otherwise>
                                </xsl:choose>
                                
                            </xsl:for-each>
                        </card>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="." />
                    </xsl:otherwise>
                </xsl:choose>
                
                
            </xsl:for-each>
        </root>
    </xsl:template>
    
    
</xsl:stylesheet>