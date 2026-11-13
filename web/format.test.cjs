const test = require("node:test");
const assert = require("node:assert/strict");
const {smartFormatsJS, formatTranscript, exampleReport} = require("./app.js");

for (const [input, expected] of [
  ["Five forty PM", "5:40 PM"],
  ["at six fifty five am", "at 6:55 AM"],
  ["Twelve thirty", "12:30"],
  ["Nine fifteen AM", "9:15 AM"],
  ["thirty one January 2026", "31 January 2026"],
  ["fifteen november 2026", "15 November 2026"],
  ["thirty one april", "thirty one april"],
  ["five hundred and twenty three rupees", "523 rupees"],
  ["zero point zero five", "0.05"],
  ["three point one four", "3.14"],
  ["five sixty PM", "five sixty PM"],
  ["I have twelve thirty apples", "I have twelve thirty apples"],
  ["one of us", "one of us"],
]) test(input, () => assert.equal(smartFormatsJS(input), expected));

test("spoken punctuation and code mode", () => {
  assert.equal(formatTranscript("hello comma how are you question mark"), "Hello, how are you?");
  assert.equal(formatTranscript("snake case user name equals five", {code:true}), "user_name = 5");
});

test("spoken list markers format a list without changing ordinary prose", () => {
  assert.equal(formatTranscript("first apples comma second bananas comma third oranges."),
    "- apples\n- bananas\n- oranges");
  assert.equal(formatTranscript("the first draft needs a second look"),
    "The first draft needs a second look.");
});

test("a copied test case preserves multiline text and the formatter settings", () => {
  const input = 'first apples\nsecond bananas\nthird "blood oranges"';
  const output = '- apples\n- bananas\n- "blood oranges"';
  assert.deepEqual(JSON.parse(exampleReport(input, output, {code: false, style: ""})),
    {input, output, mode: "dictation", style: "default"});
});
