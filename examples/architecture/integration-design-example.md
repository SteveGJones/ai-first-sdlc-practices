# Integration Design - E-Commerce Checkout System

**Project:** FastCart Checkout System  
**Version:** 1.0  
**Last Updated:** 2024-07-25  
**Author:** Integration Architecture Team

## Overview
This document details all external system integrations for the checkout system, ordered by complexity and criticality. Each integration includes contracts, failure modes, and mitigation strategies.

## Integration Complexity Matrix

| Integration | Complexity | Criticality | Risk Level | Implementation Order |
|-------------|------------|-------------|------------|---------------------|
| Stripe Payment API | High | Critical | High | 1st |
| Inventory Management | High | Critical | High | 2nd |
| Tax Calculation Service | Medium | Critical | Medium | 3rd |
| Shipping Providers | Medium | High | Medium | 4th |
| Email Service | Low | Medium | Low | 5th |
| Analytics Platform | Low | Low | Low | 6th |

## 1. Stripe Payment Processing (HARDEST - START HERE)

### Why This Is Hard
- Financial transactions require perfect accuracy
- PCI compliance requirements
- Idempotency and retry logic complexity
- Webhook reliability critical
- Multiple failure modes with money at risk

### Integration Details

#### API Endpoints
```yaml
Base URL: https://api.stripe.com/v1
Authentication: Bearer Token (Secret Key)
Rate Limits: 100 requests/second

Critical Endpoints:
  - POST /payment_intents (Create payment)
  - POST /payment_intents/{id}/confirm (Confirm payment)
  - POST /refunds (Process refund)
  - GET /payment_intents/{id} (Check status)
```

#### Request/Response Contract
```typescript
// Payment Intent Request
interface CreatePaymentIntent {
  amount: number; // in cents
  currency: 'usd' | 'eur' | 'gbp';
  payment_method_types: ['card'];
  metadata: {
    order_id: string;
    customer_id: string;
  };
  idempotency_key: string; // CRITICAL for retry safety
}

// Payment Intent Response
interface PaymentIntentResponse {
  id: string;
  status: 'requires_confirmation' | 'succeeded' | 'failed';
  amount: number;
  client_secret: string;
  created: number;
}
```

#### Webhook Contract
```typescript
interface StripeWebhook {
  id: string;
  type: 'payment_intent.succeeded' | 'payment_intent.failed' | 'charge.refunded';
  data: {
    object: PaymentIntent | Refund;
  };
  created: number;
  signature: string; // MUST verify with webhook secret
}
```

### Failure Scenarios and Mitigations

#### Scenario 1: API Timeout During Payment Creation
```typescript
async function createPaymentWithRetry(amount: number, orderId: string) {
  const idempotencyKey = `order-${orderId}-${Date.now()}`;
  const maxRetries = 3;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const payment = await stripe.paymentIntents.create({
        amount,
        currency: 'usd',
        idempotency_key: idempotencyKey,
        metadata: { order_id: orderId }
      }, {
        timeout: 10000, // 10 second timeout
      });
      return payment;
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await sleep(Math.pow(2, attempt) * 1000); // Exponential backoff
    }
  }
}
```

#### Scenario 2: Webhook Delivery Failure
```typescript
class WebhookProcessor {
  async processWebhook(event: StripeWebhook) {
    // Verify signature FIRST
    if (!this.verifySignature(event)) {
      throw new Error('Invalid webhook signature');
    }
    
    // Idempotent processing
    const processed = await db.webhookEvents.findOne({ id: event.id });
    if (processed) return; // Already processed
    
    await db.transaction(async (trx) => {
      // Record webhook
      await trx.webhookEvents.insert({ id: event.id, processed_at: new Date() });
      
      // Process based on type
      switch (event.type) {
        case 'payment_intent.succeeded':
          await this.handlePaymentSuccess(event.data.object, trx);
          break;
        case 'payment_intent.failed':
          await this.handlePaymentFailure(event.data.object, trx);
          break;
      }
    });
  }
}
```

#### Scenario 3: Partial Refund Complexity
```typescript
async function processRefund(paymentIntentId: string, amount?: number) {
  // Get original payment
  const payment = await stripe.paymentIntents.retrieve(paymentIntentId);
  
  // Validate refund amount
  const refundAmount = amount || payment.amount;
  const previousRefunds = await stripe.refunds.list({ payment_intent: paymentIntentId });
  const totalRefunded = previousRefunds.data.reduce((sum, r) => sum + r.amount, 0);
  
  if (totalRefunded + refundAmount > payment.amount) {
    throw new Error('Refund amount exceeds original payment');
  }
  
  // Process refund with idempotency
  const refund = await stripe.refunds.create({
    payment_intent: paymentIntentId,
    amount: refundAmount,
    reason: 'requested_by_customer',
    metadata: { processed_by: 'checkout_system' }
  }, {
    idempotency_key: `refund-${paymentIntentId}-${refundAmount}-${Date.now()}`
  });
  
  return refund;
}
```

### Monitoring and Alerts
```yaml
Metrics:
  - payment_creation_latency_ms
  - payment_success_rate
  - webhook_processing_delay_ms
  - refund_processing_time_ms

Alerts:
  - Payment failure rate > 5%
  - Webhook delay > 5 minutes
  - API timeout rate > 1%
  - Signature verification failures
```

## 2. Inventory Management System

### Why This Is Complex
- Real-time accuracy requirements
- Distributed system coordination
- Race conditions with concurrent orders
- Reconciliation complexity

### Integration Details

#### API Contract
```yaml
Base URL: https://inventory.internal/api/v2
Authentication: mTLS + API Key
Rate Limits: 500 requests/second

Endpoints:
  - GET /products/{sku}/availability
  - POST /reservations
  - DELETE /reservations/{id}
  - POST /orders/confirm
```

#### Reservation Flow
```typescript
interface ReservationRequest {
  items: Array<{
    sku: string;
    quantity: number;
  }>;
  reservation_duration_minutes: number;
  order_id: string;
}

interface ReservationResponse {
  reservation_id: string;
  expires_at: string;
  items: Array<{
    sku: string;
    quantity_reserved: number;
    quantity_available: number;
  }>;
}
```

### Critical Integration Pattern: Distributed Transaction
```typescript
class CheckoutOrchestrator {
  async processCheckout(order: Order) {
    let reservationId: string | null = null;
    let paymentIntentId: string | null = null;
    
    try {
      // Step 1: Reserve inventory
      const reservation = await this.inventoryService.reserve(order.items);
      reservationId = reservation.reservation_id;
      
      // Step 2: Calculate shipping and tax
      const shipping = await this.shippingService.calculate(order);
      const tax = await this.taxService.calculate(order);
      
      // Step 3: Create payment
      const payment = await this.paymentService.createIntent(
        order.total + shipping + tax
      );
      paymentIntentId = payment.id;
      
      // Step 4: Confirm payment (frontend handles 3DS)
      await this.waitForPaymentConfirmation(paymentIntentId);
      
      // Step 5: Confirm inventory
      await this.inventoryService.confirmReservation(reservationId);
      
      // Step 6: Create order record
      await this.orderService.create(order, paymentIntentId);
      
    } catch (error) {
      // Rollback in reverse order
      if (paymentIntentId) {
        await this.paymentService.cancelIntent(paymentIntentId);
      }
      if (reservationId) {
        await this.inventoryService.releaseReservation(reservationId);
      }
      throw error;
    }
  }
}
```

## 3. Tax Calculation Service

### Integration Details
```yaml
Provider: TaxJar API
Base URL: https://api.taxjar.com/v2
Authentication: Bearer Token
Rate Limits: 10,000 requests/day
```

### Smart Caching Strategy
```typescript
class TaxCalculator {
  private cache = new Redis();
  private readonly CACHE_TTL = 86400; // 24 hours
  
  async calculateTax(order: Order): Promise<TaxCalculation> {
    const cacheKey = this.generateCacheKey(order);
    
    // Try cache first
    const cached = await this.cache.get(cacheKey);
    if (cached) return JSON.parse(cached);
    
    // Call API with circuit breaker
    const tax = await this.circuitBreaker.execute(async () => {
      return this.taxjarClient.calculateTax({
        from_zip: WAREHOUSE_ZIP,
        to_zip: order.shipping_address.zip,
        to_state: order.shipping_address.state,
        amount: order.subtotal,
        shipping: order.shipping_cost
      });
    });
    
    // Cache result
    await this.cache.setex(cacheKey, this.CACHE_TTL, JSON.stringify(tax));
    
    return tax;
  }
  
  private generateCacheKey(order: Order): string {
    // Cache by zip, state, and amount (rounded to dollar)
    return `tax:${order.shipping_address.state}:${order.shipping_address.zip}:${Math.floor(order.subtotal)}`;
  }
}
```

## 4. Shipping Providers (FedEx, UPS, USPS)

### Multi-Provider Strategy
```typescript
class ShippingService {
  private providers = [
    new FedExProvider(),
    new UPSProvider(),
    new USPSProvider()
  ];
  
  async getRates(shipment: Shipment): Promise<ShippingRate[]> {
    // Parallel requests with timeout
    const promises = this.providers.map(provider => 
      this.getRateWithTimeout(provider, shipment)
    );
    
    const results = await Promise.allSettled(promises);
    
    // Filter successful responses
    const rates = results
      .filter(r => r.status === 'fulfilled')
      .map(r => (r as PromiseFulfilledResult<ShippingRate[]>).value)
      .flat()
      .sort((a, b) => a.cost - b.cost);
    
    if (rates.length === 0) {
      // Fallback to flat rate
      return this.getFlatRateOptions(shipment);
    }
    
    return rates;
  }
  
  private async getRateWithTimeout(
    provider: ShippingProvider, 
    shipment: Shipment
  ): Promise<ShippingRate[]> {
    return Promise.race([
      provider.getRates(shipment),
      this.timeout(3000).then(() => []) // 3 second timeout, return empty on timeout
    ]);
  }
}
```

## 5. Email Service (SendGrid)

### Reliable Email Delivery
```typescript
class EmailService {
  private queue = new Bull('email-queue');
  
  async sendOrderConfirmation(order: Order) {
    // Queue for reliability
    await this.queue.add('order-confirmation', {
      to: order.customer_email,
      order_id: order.id,
      template_id: 'order_confirmation_v2'
    }, {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 5000
      },
      removeOnComplete: true,
      removeOnFail: false
    });
  }
  
  // Worker process
  async processEmailJob(job: Job) {
    const { to, order_id, template_id } = job.data;
    
    try {
      await this.sendgrid.send({
        to,
        from: 'orders@fastcart.com',
        templateId: template_id,
        dynamicTemplateData: {
          order_id,
          // ... other data
        }
      });
    } catch (error) {
      if (error.response?.statusCode === 429) {
        // Rate limited, retry later
        throw new Error('Rate limited, retry needed');
      }
      // Log and don't retry for permanent failures
      console.error('Permanent email failure:', error);
    }
  }
}
```

## Integration Testing Strategy

### Contract Testing
```typescript
describe('Stripe Integration Contract', () => {
  it('should handle payment intent creation', async () => {
    const mock = nock('https://api.stripe.com')
      .post('/v1/payment_intents')
      .reply(200, mockPaymentIntentResponse);
    
    const result = await paymentService.createPayment(100);
    
    expect(result.id).toBeDefined();
    expect(mock.isDone()).toBe(true);
  });
});
```

### Chaos Testing
```yaml
Scenarios:
  - Stripe API returns 500 errors
  - Inventory service times out
  - Tax service returns invalid data
  - All shipping providers timeout
  - Database connection lost mid-transaction
```

## Monitoring Dashboard

```yaml
Key Metrics:
  - Integration success rates by provider
  - Average response times per service
  - Timeout rates
  - Fallback usage rates
  - Circuit breaker trips

Alerts:
  - Any integration < 95% success rate
  - Response time > 2x normal
  - Circuit breaker open > 5 minutes
  - Fallback usage > 10%
```

## Rollback Strategy

Each integration has a feature flag:
```typescript
if (featureFlags.isEnabled('use_new_tax_provider')) {
  return this.newTaxProvider.calculate(order);
} else {
  return this.oldTaxProvider.calculate(order);
}
```

## Security Considerations

1. **API Keys**: Stored in HashiCorp Vault, rotated monthly
2. **mTLS**: For internal service communication
3. **Request Signing**: For webhook verification
4. **Rate Limiting**: Implement client-side to prevent 429s
5. **PII Handling**: Never log sensitive data

## Success Metrics

- All integrations maintain > 99.5% availability
- P95 latency < 500ms for any integration
- Zero payment processing errors due to integration issues
- < 0.1% of orders fall back to manual processing