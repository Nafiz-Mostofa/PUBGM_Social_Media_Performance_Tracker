from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import io
from openpyxl.styles import PatternFill
from services.stats_fetcher import get_stats

router = APIRouter(
    prefix="/api/data-sheet",
    tags=["Data Sheet"]
)

class URLRequest(BaseModel):
    urls: List[str]

@router.post("/")
async def get_data_sheet_batch(request: URLRequest):
    """
    Accepts a list of social media URLs.
    Fetches stats, converts to a single DataFrame, formats as Excel,
    and returns it as a downloadable file via StreamingResponse.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided.")

    results = [get_stats(url) for url in request.urls]
        
    # Put all data into a single Pandas DataFrame
    df = pd.DataFrame(results)
    
    # Fill missing values for varying columns (e.g. facebook vs youtube)
    # Ensure DataFrame is object type before filling to avoid Numeric casting errors
    df = df.fillna('N/A')
    
    # Order columns logically if they exist
    preferred_order = ['Platform', 'Url', 'Views', 'Likes', 'Comments', 'Shares', 'Saves', 'Video_id', 'Error']
    
    # Capitalize the first letter of all column headers (e.g., 'Video_id', 'Views', 'Likes')
    df.columns = [str(col).capitalize() for col in df.columns]
    
    # Reorder columns that are present
    existing_columns = [col for col in preferred_order if col in df.columns]
    other_columns = [col for col in df.columns if col not in preferred_order]
    df = df[existing_columns + other_columns]
    
    # Use pandas.ExcelWriter with the openpyxl engine to write to a BytesIO buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Social Stats')
        
        workbook = writer.book
        worksheet = writer.sheets['Social Stats']
        
        # Apply a light yellow background color to the header row
        # FFFFCC is a standard light yellow HEX color
        light_yellow_fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        for cell in worksheet[1]:  # Row 1 is the header row
            cell.fill = light_yellow_fill
            
            # Ensure column widths are adjusted slightly for readability
            # Setting a fixed width to 25 mapping roughly to typical characters padding
            column_letter = cell.column_letter
            worksheet.column_dimensions[column_letter].width = 25
            
    # Reset file pointer to the beginning to allow StreamingResponse to read it
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="social_stats_batch.xlsx"'
    }
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )
