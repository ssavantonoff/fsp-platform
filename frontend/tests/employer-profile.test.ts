import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { EmployerProfileView } from "../src/components/employer-screen";
import type { EmployerProfile } from "../src/types";

const profile: EmployerProfile = {
  id: "employer-profile",
  user_id: "employer-user",
  company_name: "Компания ФСП",
  company_description: "Создаём платформу\nдля профессионального развития.",
  website: "https://example.com/company",
  contact_person_name: "Ирина Петрова",
};

function view(overrides: Partial<EmployerProfile> = {}) {
  return renderToStaticMarkup(
    createElement(EmployerProfileView, { profile: { ...profile, ...overrides } }),
  );
}

test("employer dashboard shows company details and existing workflow routes", () => {
  const html = view();
  assert.match(html, /<h1>Компания ФСП<\/h1>/);
  assert.match(html, /aria-label="О компании"/);
  assert.ok(html.includes(profile.company_description!));
  assert.match(html, /Контактное лицо<\/dt><dd>Ирина Петрова<\/dd>/);
  assert.match(html, /href="https:\/\/example\.com\/company" target="_blank" rel="noopener noreferrer"/);
  assert.match(html, /class="button" href="\/employer\/needs">Потребности компании<\/a>/);
  assert.match(html, /class="button secondary" href="\/employer\/edit">Редактировать профиль<\/a>/);
  assert.equal((html.match(/href="\/employer\/needs"/g) ?? []).length, 1);
  assert.equal((html.match(/href="\/employer\/edit"/g) ?? []).length, 1);
});

test("employer dashboard represents empty optional fields without fabricated links", () => {
  for (const empty of [null, ""]) {
    const html = view({ company_description: empty, website: empty });
    assert.match(html, /Описание компании не указано\./);
    assert.match(html, /Сайт<\/dt><dd>Не указан<\/dd>/);
    assert.doesNotMatch(html, /target="_blank"|href=""|undefined|>null</);
    assert.match(html, /href="\/employer\/needs"/);
  }
});

test("employer dashboard escapes user content and retains long company details", () => {
  const description = "Подробности компании ".repeat(120) + "<script>unsafe()</script>";
  const html = view({
    company_name: "<b>Компания</b>",
    company_description: description,
    contact_person_name: "<img src=x onerror=unsafe()>",
  });
  assert.match(html, /<h1>&lt;b&gt;Компания&lt;\/b&gt;<\/h1>/);
  assert.ok(html.includes(description.replaceAll("<", "&lt;").replaceAll(">", "&gt;")));
  assert.match(html, /&lt;img src=x onerror=unsafe\(\)&gt;/);
  assert.doesNotMatch(html, /<script>|<b>Компания|<img/);
});

test("employer dashboard renders only permitted profile fields", () => {
  const html = view({
    ...profile,
    ...{
      email: "private@example.com",
      phone: "+79999999999",
      password: "private-password",
    },
  });
  assert.doesNotMatch(html, /employer-profile|employer-user|private@example\.com|79999999999|private-password/);
});
