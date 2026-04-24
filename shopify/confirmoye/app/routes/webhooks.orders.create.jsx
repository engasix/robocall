import { authenticate } from "../shopify.server";

export const action = async ({ request }) => {
  const { shop, payload } = await authenticate.webhook(request);

  const order = payload;

  console.log("=== NEW ORDER WEBHOOK ===");
  console.log("Shop:", shop);
  console.log("Order ID:", order.id);
  console.log("Order Number:", order.order_number);
  console.log("Payment Gateway:", order.payment_gateway);
  console.log("Gateway:", order.gateway);
  console.log("Total Price:", order.total_price, order.currency);
  console.log("Phone (order):", order.phone);
  console.log("Customer:", JSON.stringify(order.customer, null, 2));
  console.log("Billing Address:", JSON.stringify(order.billing_address, null, 2));
  console.log("Shipping Address:", JSON.stringify(order.shipping_address, null, 2));
  console.log("========================");

  return new Response(null, { status: 200 });
};
