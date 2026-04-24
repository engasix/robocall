import { authenticate } from "../shopify.server";
import db from "../db.server";

export const action = async ({ request }) => {
  const { shop, payload } = await authenticate.webhook(request);

  const order = payload;

  // Only process COD orders
  const isCOD =
    order.payment_gateway === "cash_on_delivery" ||
    order.gateway === "cash_on_delivery" ||
    order.payment_gateway?.toLowerCase().includes("cod");

  if (!isCOD) {
    return new Response(null, { status: 200 });
  }

  // Get store API key from settings
  const settings = await db.settings.findUnique({ where: { shop } });

  if (!settings?.apiKey || !settings?.enabled) {
    return new Response(null, { status: 200 });
  }

  // Forward to Python API
  try {
    await fetch(`${process.env.API_URL}/v1/orders/trigger`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": settings.apiKey,
      },
      body: JSON.stringify({
        shop,
        shopify_order_id: order.id,
        order_number: order.order_number,
        customer_name:
          order.customer?.first_name || order.billing_address?.first_name || "",
        phone:
          order.phone ||
          order.billing_address?.phone ||
          order.customer?.phone ||
          "",
        amount: order.total_price,
        currency: order.currency,
      }),
    });
  } catch (error) {
    // Log but don't fail — Shopify will retry on non-200 responses
    console.error(`[orders/create] Failed to forward order ${order.id}:`, error);
  }

  return new Response(null, { status: 200 });
};
