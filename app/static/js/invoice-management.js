$(document).ready(function() {
    // Form submit işlemi
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault(); // Sayfanın yenilenmesini engelle
        console.log('Form submitted');
        
        // Loading göster
        $('#loading').show();
        
        // Form verilerini al
        const formData = new FormData(this);
        
        // AJAX isteği
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#loading').hide();
                
                if (response.success) {
                    // Fatura listesine ekle
                    const invoiceRow = {
                        id: response.invoice_id,
                        date: response.invoice_data.date,
                        vendor: response.invoice_data.vendor,
                        amount: response.invoice_data.amount,
                        category: response.invoice_data.category,
                        filename: response.filename,
                        file_url: response.file_url,
                        invoice_number: response.invoice_data.invoice_number,
                        tax_id: response.invoice_data.tax_id,
                        tax_amount: response.invoice_data.tax_amount,
                        raw_text: response.text
                    };
                    
                    addInvoiceToList(invoiceRow);
                    
                    // Form'u temizle
                    $('#uploadForm')[0].reset();
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'Success',
                        text: 'Invoice processed successfully'
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Processing Error',
                        text: response.error || 'An error occurred'
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Ajax error:', error);
                console.error('Response:', xhr.responseText);
                $('#loading').hide();
                
                let errorMessage = 'Failed to upload invoice';
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.error) {
                        errorMessage = response.error;
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
                
                Swal.fire({
                    icon: 'error',
                    title: 'Upload Error',
                    text: errorMessage
                });
            }
        });
    });

    // Fatura listesine ekle
    function addInvoiceToList(invoice) {
        // Önceki seçili satırın vurgusunu kaldır
        $('.selected-invoice').removeClass('selected-invoice');
        
        const row = `
            <tr class="selected-invoice">
                <td class="invoice-date">${invoice.date}</td>
                <td class="vendor-name">${invoice.vendor}</td>
                <td class="total-amount">${invoice.amount}</td>
                <td><span class="badge bg-primary invoice-category">${invoice.category}</span></td>
                <td>${invoice.filename}</td>
                <td><span class="badge bg-success">Processed</span></td>
                <td>
                    <button class="btn btn-sm btn-info view-btn" 
                            data-file-url="${invoice.file_url}"
                            data-filename="${invoice.filename}"
                            data-invoice-number="${invoice.invoice_number}"
                            data-date="${invoice.date}"
                            data-category="${invoice.category}"
                            data-vendor="${invoice.vendor}"
                            data-tax-id="${invoice.tax_id}"
                            data-tax-amount="${invoice.tax_amount}"
                            data-total-amount="${invoice.amount}"
                            data-raw-text="${invoice.raw_text}">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-danger delete-btn" data-id="${invoice.id}">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
        $('#invoiceList').prepend(row);

        // Yeni eklenen faturanın detaylarını otomatik olarak göster
        const newRow = $('#invoiceList tr:first');
        const viewBtn = newRow.find('.view-btn');
        
        // Detay panelini güncelle
        $('#originalImage').attr('src', invoice.file_url);
        $('#originalImage').attr('alt', invoice.filename);
        $('#fileName').text(invoice.filename);
        
        // Temel bilgileri güncelle
        $('#invoiceNumber').text(invoice.invoice_number);
        $('#invoiceDate').text(invoice.date);
        $('#category').text(invoice.category);
        
        // Şirket bilgileri
        $('#vendorName').text(invoice.vendor);
        $('#taxId').text(invoice.tax_id);
        
        // Finansal bilgiler
        $('#taxAmount').text(invoice.tax_amount + ' RM');
        $('#totalAmount').text(invoice.amount);
        
        // Ham OCR metni
        $('#rawText').text(invoice.raw_text);
        
        // Detay panelini göster
        $('#invoiceDetails').show();
        
        // Sayfayı detaylara kaydır
        $('html, body').animate({
            scrollTop: $("#invoiceDetails").offset().top
        }, 500);
    }

    // View butonu için event listener
    $(document).on('click', '.view-btn', function() {
        // Önceki seçili satırın vurgusunu kaldır
        $('.selected-invoice').removeClass('selected-invoice');
        
        // Tıklanan satırı vurgula
        $(this).closest('tr').addClass('selected-invoice');
        
        const btn = $(this);
        const fileUrl = btn.data('file-url');
        const filename = btn.data('filename');
        
        // Detay panelini güncelle
        $('#originalImage').attr('src', fileUrl);
        $('#originalImage').attr('alt', filename);
        $('#fileName').text(filename);
        
        // Temel bilgileri güncelle
        $('#invoiceNumber').text(btn.data('invoice-number'));
        $('#invoiceDate').text(btn.data('date'));
        $('#category').text(btn.data('category'));
        
        // Şirket bilgileri
        $('#vendorName').text(btn.data('vendor'));
        $('#taxId').text(btn.data('tax-id'));
        
        // Finansal bilgiler
        $('#taxAmount').text(btn.data('tax-amount') + ' RM');
        $('#totalAmount').text(btn.data('total-amount') + ' RM');
        
        // Ham OCR metni
        $('#rawText').text(btn.data('raw-text'));
        
        // Detay panelini göster
        $('#invoiceDetails').show();
        
        // Sayfayı detaylara kaydır
        $('html, body').animate({
            scrollTop: $("#invoiceDetails").offset().top
        }, 500);
    });

    // Görüntüye tıklandığında büyüt
    $(document).on('click', '#originalImage', function() {
        const src = $(this).attr('src');
        const filename = $(this).attr('alt');
        
        Swal.fire({
            title: filename,
            imageUrl: src,
            imageWidth: 800,
            imageHeight: 'auto',
            imageAlt: filename,
            showCloseButton: true,
            showConfirmButton: false
        });
    });

    // Delete butonu için event listener
    $(document).on('click', '.delete-btn', function() {
        const row = $(this).closest('tr');
        const invoiceId = $(this).data('id');
        
        Swal.fire({
            title: 'Are you sure?',
            text: "You won't be able to revert this!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!'
        }).then((result) => {
            if (result.isConfirmed) {
                // AJAX ile silme isteği gönder
                $.ajax({
                    url: `/delete/${invoiceId}`,
                    type: 'DELETE',
                    success: function(response) {
                        if (response.success) {
                            // Satırı tablodan kaldır
                            row.remove();
                            
                            // Eğer silinen fatura detayları görüntüleniyorsa, detay panelini gizle
                            if (row.hasClass('selected-invoice')) {
                                $('#invoiceDetails').hide();
                            }
                            
                            Swal.fire(
                                'Deleted!',
                                'Invoice has been deleted.',
                                'success'
                            );
                        } else {
                            Swal.fire(
                                'Error!',
                                response.error || 'Failed to delete invoice',
                                'error'
                            );
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Delete error:', error);
                        Swal.fire(
                            'Error!',
                            'Failed to delete invoice',
                            'error'
                        );
                    }
                });
            }
        });
    });

    // Arama ve filtreleme
    $('#searchInput').on('keyup', function() {
        const searchText = $(this).val().toLowerCase();
        $('#invoiceList tr').each(function() {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(searchText));
        });
    });

    $('#categoryFilter').on('change', function() {
        const category = $(this).val().toLowerCase();
        if (category === '') {
            $('#invoiceList tr').show();
        } else {
            $('#invoiceList tr').each(function() {
                const rowCategory = $(this).find('td:eq(3)').text().toLowerCase();
                if (category === 'others') {
                    // Others kategorisi için, bilinen kategorilerde olmayan faturaları göster
                    const isOther = !['service', 'purchase', 'utility'].includes(rowCategory);
                    $(this).toggle(isOther);
                } else {
                    // Diğer kategoriler için normal filtreleme
                    $(this).toggle(rowCategory === category);
                }
            });
        }
    });

    // Tarih filtresi
    function updateDateFilter() {
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        if (!startDate || !endDate) return;
        
        $('#invoiceList tr').each(function() {
            const invoiceDate = $(this).find('td:eq(0)').text();
            const date = new Date(invoiceDate);
            const show = date >= new Date(startDate) && date <= new Date(endDate);
            $(this).toggle(show);
        });
    }

    $('#startDate, #endDate').on('change', updateDateFilter);
}); 