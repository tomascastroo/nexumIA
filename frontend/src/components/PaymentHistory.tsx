import React, { useState, useEffect } from 'react';
import { paymentLinkService, DebtPayment } from '../services/paymentLinkService';

interface PaymentHistoryProps {
  debtorId: number;
}

const PaymentHistory: React.FC<PaymentHistoryProps> = ({ debtorId }) => {
  const [payments, setPayments] = useState<DebtPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPaymentHistory();
  }, [debtorId]);

  const loadPaymentHistory = async () => {
    try {
      setLoading(true);
      setError('');
      const history = await paymentLinkService.getPaymentHistory(debtorId);
      setPayments(history);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-12 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-600 text-center">{error}</div>
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div className="p-4">
        <div className="text-gray-500 text-center">
          No hay historial de pagos para este deudor.
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Historial de Pagos</h3>
      <div className="space-y-3">
        {payments.map((payment) => (
          <div key={payment.id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(payment.status)}`}>
                    {payment.status === 'paid' ? 'Pagado' :
                     payment.status === 'pending' ? 'Pendiente' :
                     payment.status === 'failed' ? 'Fallido' :
                     payment.status === 'expired' ? 'Expirado' : payment.status}
                  </span>
                  {payment.method && (
                    <span className="text-xs text-gray-500">
                      {payment.method.toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-600">
                  Creado: {formatDate(payment.created_at)}
                </div>
                {payment.expires_at && (
                  <div className="text-sm text-gray-600">
                    Expira: {formatDate(payment.expires_at)}
                  </div>
                )}
              </div>
              <div className="text-right">
                <div className="font-semibold text-lg">
                  {formatAmount(payment.amount_requested)}
                </div>
                {payment.discount_applied && (
                  <div className="text-sm text-green-600">
                    Descuento: {payment.discount_applied}%
                  </div>
                )}
              </div>
            </div>
            
            {payment.payment_link && (
              <div className="mt-2">
                <a
                  href={payment.payment_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm break-all"
                >
                  {payment.payment_link}
                </a>
              </div>
            )}
            
            {payment.amount_paid && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <div className="text-sm text-gray-600">
                  Pagado: {formatAmount(payment.amount_paid)}
                </div>
                {payment.paid_at && (
                  <div className="text-sm text-gray-600">
                    Fecha de pago: {formatDate(payment.paid_at)}
                  </div>
                )}
              </div>
            )}
            
            {payment.external_reference && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <div className="text-xs text-gray-500">
                  Referencia: {payment.external_reference}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PaymentHistory; 