<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0">
	<!-- Identity template to copy all other nodes as is -->
	<xsl:template match="@* | node()">
		<xsl:copy>
			<xsl:apply-templates select="@* | node()"/>
		</xsl:copy>
	</xsl:template>
	
	<!-- Template to match <wordLink> elements -->
	<xsl:template match="wordLink">
		<xsl:variable name="wordWithHomonym">
			<xsl:choose>
				<xsl:when test="@homonym != ''">
					<xsl:value-of select="concat(@word, ' ', @homonym)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="@word"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="wordWithHomonymAndMeaning">
			<xsl:choose>
				<xsl:when test="@meaning != ''">
					<xsl:value-of select="concat($wordWithHomonym, ' ', @meaning)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$wordWithHomonym"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		
		<a>
			<!-- Copy the "word" attribute -->
			<xsl:attribute name="href">
				<xsl:value-of select="concat('x-dictionary:r:', $wordWithHomonym)"/>
			</xsl:attribute>
			<xsl:value-of select="$wordWithHomonymAndMeaning" />
		</a>
	</xsl:template>
</xsl:stylesheet>