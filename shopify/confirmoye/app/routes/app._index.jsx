import { useLoaderData, useNavigate } from "react-router";
import { boundary } from "@shopify/shopify-app-react-router/server";
import { authenticate } from "../shopify.server";
import db from "../db.server";

export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const shop = session.shop;

  const settings = await db.settings.findUnique({ where: { shop } });

  if (!settings?.apiKey) {
    return { orders: [], noApiKey: true, error: null };
  }

  try {
    const response = await fetch(
      `${process.env.API_URL}/v1/orders?shop=${shop}`,
      {
        headers: { "X-Api-Key": settings.apiKey },
      }
    );

    if (!response.ok) {
      return { orders: [], noApiKey: false, error: "Failed to fetch orders from API." };
    }

    const orders = await response.json();
    return { orders, noApiKey: false, error: null };
  } catch {
    return { orders: [], noApiKey: false, error: "Could not connect to ConfirmOye API." };
  }
};

export default function Index() {
  const { orders, noApiKey, error } = useLoaderData();
  const navigate = useNavigate();

  if (noApiKey) {
    return (
      <s-page heading="Orders">
        <s-section heading="Setup required">
          <s-paragraph>
            You need to configure your API key before orders can be tracked.
            Click the button below to go to Settings.
          </s-paragraph>
          <s-button onClick={() => navigate("/app/settings")}>
            Go to Settings
          </s-button>
        </s-section>
      </s-page>
    );
  }

  return (
    <s-page heading="Orders">
      {error && (
        <s-section>
          <s-paragraph>{error}</s-paragraph>
        </s-section>
      )}

      {!error && orders.length === 0 && (
        <s-section heading="No orders yet">
          <s-paragraph>
            Orders will appear here once customers start placing COD orders.
          </s-paragraph>
        </s-section>
      )}

      {orders.length > 0 && (
        <s-section>
          <s-data-table
            columnContentTypes={["text", "text", "text", "numeric", "numeric"]}
            headings={["Order", "Customer", "Status", "Amount", "Attempts"]}
            rows={orders.map((order) => [
              `#${order.shopify_order_id}`,
              order.customer_name,
              order.status,
              `PKR ${order.amount}`,
              String(order.call_attempts ?? 0),
            ])}
          />
        </s-section>
      )}
    </s-page>
  );
}

export const headers = (headersArgs) => {
  return boundary.headers(headersArgs);
};
