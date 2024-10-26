from openai import OpenAI
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

client = OpenAI()

prompt = """
You are a lexicographer.
You are working on improving an existing Kyrgyz-Russian dictionary by Konstantin Yudakhin.
The dictionary has been scanned and converted into a giant XML file, and while it’s readable, it does contain a small amount of scanning errors.
You will receive <card>
Here’s the description of the XML structure:
Each entry is enclosed in a <card> tag.
Inside every <card>, the very first tag you’ll see is a required <k> tag, which contains a header word.
You might also encounter <meta> and <origin> tags, they contain conditional abbreviations.
You might also encounter <meaning> tags which contain different meanings of the header word (in case there’s more than one).
The rest of the text will come in <blockquote> tags.

So, an example of an entry would look like this:
    <card>
        <k>ада</k>
        <origin>ар.</origin>
        <meaning>
            <blockquote>1. конец, окончание, завершение; иссякание;</blockquote>
            <blockquote>ада бол- закончиться, кончиться; иссякнуть;</blockquote>
            <blockquote>ада бол! пропади ты!;</blockquote>
            <blockquote>ада кыл- кончить, закончить, завершить; довести до иссякания;</blockquote>
            <blockquote>малдын барын түгөтүп, ада кылды жанбакты стих. извёл и прикончил весь скот, бездельник;</blockquote>
        </meaning>
        <meaning>
            <blockquote>2. выполнение, исполнение;</blockquote>
            <blockquote>ада болсо если исполнится (свершится).</blockquote>
        </meaning>
    </card>

Your job is to detect whether contents of a <blockquote> tag is a usage example of the header word.

Hints to help you identify a usage example:
1. Content begins with text in Kyrgyz.
2. Content ends with text in Russian.
3. There may be conditional abbreviations in the middle of the line, such as “миф.”, “стих.”, “южн.” and others
4. Most likely, content will contain a word very similar to the header word.

If you’re sure the line contains a usage example, then:
1. Replace the <blockquote> tag with <ex>.
2. Enclose the Kyrgyz text in the <source> tag.
3. Enclose the Russian text in the <target> tag.
4. Place the conditional abbreviations (such as “миф.”, “стих.”, “южн.” and others) inside the <target> tag along with the Russian text.

So, an ideally marked version of an example above would look like this:

    <card>
        <k>ада</k>
        <origin>ар.</origin>
        <meaning>
            <trn>1. конец, окончание, завершение; иссякание;</trn>
            <ex>
                <source>ада бол-</source>
                <target>закончиться, кончиться; иссякнуть;</target>
            </ex>
            <ex>
                <source>ада бол!</source>
                <target>пропади ты!;</target>
            </ex>
            <ex>
                <source>ада кыл-</source>
                <target>кончить, закончить, завершить; довести до иссякания;</target>
            </ex>
            <ex>
                <source>малдын барын түгөтүп, ада кылды жанбакты</source> 
                <target>стих. извёл и прикончил весь скот, бездельник;</target>
            </ex>
        </meaning>
        <meaning>
            <trn>2. выполнение, исполнение;</trn>
            <ex>
                <source>ада болсо</source>
                <target>если исполнится (свершится).</target>
            </ex>
        </meaning>
    </card>
    
Your response must not contain markdown, return XML only
"""

with open(inputFilename, 'r', encoding='utf-8') as file:
    inputContent = file.read()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
    {
      "role": "system",
      "content": prompt
    },
    {
      "role": "user",
      "content": inputContent
    }
	]
)

# Accessing the correct part of the completion response
output = completion.choices[0].message.content

# Write the output to a file
with open(outputFilename, "w", encoding="utf-8") as file:
    file.write(output)