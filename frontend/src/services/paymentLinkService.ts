import { API_BASE_URL } from '../shared/config';

export interface PaymentLinkEligibility {
  debtor_id: number;
  debtor_state: string;
  should_generate: boolean;
  reason: string;
  data: any;
  message: string;
}

export interface PaymentRequest {
  debtor_id: number;
  amount_requested: number;
  discount_applied?: number;
  campaign_id?: number;
  rule_id?: string;
  method?: string;
}

export interface DebtPayment {
  id: number;
  debtor_id: number;
  amount_requested: number;
  amount_paid?: number;
  discount_applied?: number;
  status: string;
  payment_link?: string;
  method?: string;
  external_reference?: string;
  paid_at?: string;
  created_at: string;
  expires_at?: string;
  campaign_id?: number;
  rule_id?: string;
}

class PaymentLinkService {
  private baseUrl = `${API_BASE_URL}/debt_payment`;

  async checkEligibility(debtorId: number, userMessage: string): Promise<PaymentLinkEligibility> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${this.baseUrl}/check-eligibility/${debtorId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ user_message: userMessage })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error checking payment link eligibility');
    }

    return response.json();
  }

  async generatePaymentLink(request: PaymentRequest): Promise<DebtPayment> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${this.baseUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error generating payment link');
    }

    return response.json();
  }

  async getPaymentHistory(debtorId: number): Promise<DebtPayment[]> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${this.baseUrl}/history/${debtorId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error fetching payment history');
    }

    return response.json();
  }

  async confirmPayment(paymentId: number, amountPaid: number): Promise<DebtPayment> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${this.baseUrl}/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ 
        payment_id: paymentId, 
        amount_paid: amountPaid 
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error confirming payment');
    }

    return response.json();
  }

  // Método para analizar si un mensaje solicita un link de pago
  analyzePaymentLinkRequest(message: string): boolean {
    const paymentKeywords = [
      'link de pago',
      'link para pagar',
      'enlace de pago',
      'enlace para pagar',
      'link',
      'enlace',
      'pagar',
      'quiero pagar',
      'dame el link',
      'envíame el link',
      'mandame el link',
      'dame el enlace',
      'envíame el enlace',
      'mandame el enlace',
      'cómo pago',
      'donde pago',
      'pago online',
      'pago por internet',
      'transferencia',
      'débito',
      'crédito',
      'tarjeta',
      'mercadopago',
      'paypal',
      'stripe'
    ];

    const normalizedMessage = message.toLowerCase().trim();
    return paymentKeywords.some(keyword => normalizedMessage.includes(keyword));
  }

  // Método para generar respuesta según el estado del deudor
  generateResponseByState(
    state: string, 
    debtAmount: number, 
    shouldGenerate: boolean, 
    reason: string
  ): string {
    const formattedAmount = new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(debtAmount);

    switch (state) {
      case 'VERDE':
        if (shouldGenerate) {
          return `Gracias por tu predisposición. Enseguida te comparto el link para regularizar la deuda.

Tu deuda es de ${formattedAmount} y el link vence en 48 horas.

Link de pago: [GENERAR_LINK_AQUI]

Recordá que el link vence en 48 horas. Si tenés alguna consulta, no dudes en preguntarme.`;
        }
        return `Gracias por tu interés. Tu deuda es de ${formattedAmount}. ¿Querés que te envíe el link para pagar?`;

      case 'AMARILLO':
        if (shouldGenerate) {
          return `Entiendo tu situación. ¿Querés que te envíe el link con el descuento vigente?

Tu deuda es de ${formattedAmount} y tenemos opciones de descuento disponibles.

¿Querés que te lo envíe ahora mismo por este medio?`;
        }
        return `Entiendo tu situación. Tu deuda es de ${formattedAmount}. ¿Querés que te envíe el link para pagar?`;

      case 'ROJO':
        return `Entiendo tu situación. Un especialista se pondrá en contacto contigo para ayudarte.`;

      case 'GRIS':
        return `Gracias por tu interés. Un especialista se pondrá en contacto contigo.`;

      default:
        return `Gracias por tu interés. Un especialista se pondrá en contacto contigo.`;
    }
  }
}

export const paymentLinkService = new PaymentLinkService(); 