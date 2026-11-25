import assert from "node:assert/strict";
import test from "node:test";
import { pickGame } from "../../src/lib/pick.ts";

const games = [
  { appid: "35140", installed: true },
  { appid: "12140", installed: true },
  { appid: "12150", installed: false },
];

test("nothing to pick from an empty list", () => assert.equal(pickGame([], null), null));
test("first installed game when nothing is remembered", () => assert.equal(pickGame(games, null), "35140"));
test("the remembered game wins, so a remounted panel keeps the choice", () => {
  assert.equal(pickGame(games, "12140"), "12140");
  assert.equal(pickGame(games, "12150"), "12150");
});
test("a remembered game that left the list falls back", () => assert.equal(pickGame(games, "999"), "35140"));
test("no installed game: the first of the list", () =>
  assert.equal(pickGame([{ appid: "1", installed: false }, { appid: "2", installed: false }], null), "1"));
