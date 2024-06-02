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
				<xsl:variable name="homonymRegex" select="'^(\w+)(-)? (I|II|III|IV|V|VI|VII|VIII|IX|X):?$'"/>
				<xsl:variable name="firstBlockquote" select="blockquote[1]"/>
				<xsl:choose>
					<xsl:when test="matches(string($firstBlockquote), $homonymRegex)">
						<xsl:text>openingCardTag</xsl:text>
						<k><xsl:value-of select="$firstBlockquote"/></k>
						<xsl:for-each select="blockquote[position() > 1]">
							<xsl:variable name="blockquoteContent" select="."/>
							<xsl:choose>
								<xsl:when test="matches(string($blockquoteContent), $homonymRegex)">
									<xsl:text>closingCardTag</xsl:text>
									<xsl:text>openingCardTag</xsl:text>
									<k><xsl:value-of select="$blockquoteContent"/></k>
								</xsl:when>
								<xsl:otherwise>
									<xsl:copy-of select="." />
								</xsl:otherwise>
							</xsl:choose>
						</xsl:for-each>
						<xsl:text>closingCardTag</xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy-of select="." />
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</root>
	</xsl:template>
</xsl:stylesheet>