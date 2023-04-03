<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="2.0"
    xmlns:foo="http://whatever">
    <xsl:strip-space elements="*"/>
    <xsl:output method="xml" indent="yes" />
    
    <xsl:variable name="finishedLetters" select="('в', 'г', 'е', 'з', 'и', 'й', 'л', 'н', 'п', 'у', 'ү', 'ф', 'х', 'ц', 'щ', 'ю', 'я')" />
    <xsl:variable name="root-document" select="/"/>
    
    <xsl:template match="/">
        <xsl:text>&#xa;</xsl:text>
        <xsl:copy-of select="foo:printGlobalFinishedCounters()" />
    </xsl:template>
    
    <xsl:function name="foo:printGlobalFinishedCounters">
        <xsl:text>Total words in finished letters - </xsl:text>
        <xsl:value-of select="sum(for $i in $finishedLetters return count($root-document/root/card[starts-with(k, $i)]))"/>
        <xsl:text>&#xa;&#xa;</xsl:text>
        
        <xsl:for-each select="$finishedLetters">
            <xsl:variable name="currentLetter" select="." />
            <xsl:value-of select="$currentLetter" />
            <xsl:text> – </xsl:text>
            <xsl:value-of select="count($root-document/root/card[starts-with(k, $currentLetter)])" />                        
            <xsl:text> entries</xsl:text>
            <xsl:text>&#xa;</xsl:text>
        </xsl:for-each>
    </xsl:function>
    
</xsl:stylesheet>