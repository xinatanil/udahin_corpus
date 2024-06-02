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
	
	<xsl:function name="foo:separateMeanings">
		<xsl:param name="passedNode" />
		<xsl:for-each select="$passedNode/*">
			<xsl:choose>
				<xsl:when test="name() = 'k'">
				</xsl:when>
				<xsl:when test='matches(., "\d\.:? .+") and position() = last()' >
					<xsl:text>&#xa;</xsl:text>
					<xsl:text>closingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
					<xsl:text>openingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
					<xsl:copy-of select="." />
					<xsl:text>closingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
				</xsl:when>
				<xsl:when test='matches(., "1\.:? .+")' >
					<xsl:text>&#xa;</xsl:text>
					<xsl:text>openingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
					<xsl:copy-of select="." />
				</xsl:when>
				<xsl:when test='
					matches(., "2\. .+") or 
					matches(., "3\. .+") or
					matches(., "4\. .+") or
					matches(., "5\. .+") or
					matches(., "6\. .+") or
					matches(., "7\. .+")' >
					<xsl:text>&#xa;</xsl:text>
					<xsl:text>closingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
					<xsl:text>openingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
					<xsl:copy-of select="." />
				</xsl:when>
				<xsl:when test="position() = last()" >
					<xsl:copy-of select="." />
					<xsl:text>&#xa;</xsl:text>
					<xsl:text>closingMeaningTag</xsl:text>
					<xsl:text>&#xa;</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:copy-of select="." />
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:function>
	
	<xsl:template match="/root">
		<root>
			<xsl:text>&#xa;</xsl:text>
			<xsl:for-each select="card">
				<xsl:choose>
					<xsl:when test="blockquote[matches(., '\d\.:? .+')]">
						<card>
							<xsl:copy-of select="k" />
							<xsl:copy-of select="foo:separateMeanings(.)" />
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
