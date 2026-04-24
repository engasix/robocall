import { useState } from "react";
import { useFetcher, useLoaderData } from "react-router";
import { boundary } from "@shopify/shopify-app-react-router/server";
import { authenticate } from "../shopify.server";
import db from "../db.server";

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  const settings = await db.settings.findUnique({ where: { shop } });

  return { shop, settings };
};

export const action = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  const formData = await request.formData();
  const apiKey = formData.get("apiKey");
  const enabled = formData.get("enabled") === "true";

  await db.settings.upsert({
    where: { shop },
    update: { apiKey, enabled },
    create: { shop, apiKey, enabled },
  });

  return { success: true };
};

export default function Settings() {
  const { settings } = useLoaderData();
  const fetcher = useFetcher();

  const [apiKey, setApiKey] = useState(settings?.apiKey ?? "");
  const [enabled, setEnabled] = useState(settings?.enabled ?? true);

  const isSaving =
    ["loading", "submitting"].includes(fetcher.state) &&
    fetcher.formMethod === "POST";

  const handleSave = () => {
    fetcher.submit(
      { apiKey, enabled: String(enabled) },
      { method: "POST" }
    );
  };

  return (
    <s-page heading="Settings">
      <s-button
        slot="primary-action"
        onClick={handleSave}
        {...(isSaving ? { loading: true } : {})}
      >
        Save
      </s-button>

      <s-section heading="API Configuration">
        <s-paragraph>
          Enter the API key issued by ConfirmOye for your store. This connects
          your Shopify orders to the call confirmation system.
        </s-paragraph>
        <s-text-field
          label="API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk_live_xxxxxxxxxxxx"
          type="password"
        />
      </s-section>

      <s-section heading="Service">
        <s-paragraph>
          When enabled, a confirmation call will be placed automatically for
          every new Cash on Delivery order.
        </s-paragraph>
        <s-checkbox
          label="Enable call confirmation for new COD orders"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
      </s-section>

      {fetcher.data?.success && (
        <s-section>
          <s-paragraph>Settings saved successfully.</s-paragraph>
        </s-section>
      )}
    </s-page>
  );
}

export const headers = (headersArgs) => {
  return boundary.headers(headersArgs);
};
