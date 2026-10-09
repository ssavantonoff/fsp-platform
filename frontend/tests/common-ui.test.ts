import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import Home from "../src/app/page";
import NotFound from "../src/app/not-found";
import ErrorPage from "../src/app/error";

test("home keeps existing registration and login routes with accessible actions", () => {
  const html = renderToStaticMarkup(createElement(Home));
  assert.match(html, /<h1>Платформа ФСП<\/h1>/);
  assert.match(html, /class="button" href="\/register"/);
  assert.match(html, /class="button secondary" href="\/login"/);
});

test("not found offers the existing home route without inventing recovery flows", () => {
  const html = renderToStaticMarkup(createElement(NotFound));
  assert.match(html, /Страница не найдена/);
  assert.match(html, /class="button secondary" href="\/"/);
});

test("page error announces failure and exposes retry without sensitive diagnostics", () => {
  const html = renderToStaticMarkup(createElement(ErrorPage, { reset: () => {} }));
  assert.match(html, /role="alert"/);
  assert.match(html, /<button>Повторить<\/button>/);
  assert.doesNotMatch(html, /stack|token|password/);
});
